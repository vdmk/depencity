import ast
import pickle
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from depencity._graph import graph_builder
from depencity._graph.export.json import to_dict
from depencity._graph.graph_builder import lower
from depencity._graph.ir_builder import (
    build_resolved_ir,
    remove_resolved_scope_bindings,
    resolve,
    resolve_read_occurrences,
)
from depencity._graph.model.enums import NodeKind
from depencity._graph.scope_builder import build_ir
from depencity._package_graph import package_builder
from depencity._profile.classifier import profile
from depencity._profile.summary import summarize

from .integration.utils import walk_scope_tree

FIXTURES = Path(__file__).parent / 'fixtures' / 'builder'


def test_analysis_and_resolution_do_not_allocate_graph_objects(monkeypatch):
    source = (FIXTURES / 'expressions' / 'input.py').read_text()

    def reject_allocation(*args, **kwargs):
        raise AssertionError('graph allocation before IR completion')

    monkeypatch.setattr(graph_builder, 'Node', reject_allocation)
    monkeypatch.setattr(graph_builder, 'Scope', reject_allocation)
    records = build_resolved_ir(ast.parse(source))

    assert any(record.nodes for record in records)


def test_lowering_is_repeatable_and_does_not_share_mutable_ir_state():
    records = build_resolved_ir(ast.parse((FIXTURES / 'recursive_flows' / 'input.py').read_text()))
    original_ir = pickle.dumps(records)

    first = lower(records)
    expected = to_dict(first)
    second = lower(records)

    assert to_dict(second) == expected
    assert pickle.dumps(records) == original_ir
    for scope, other in zip(first.walk_scopes(), second.walk_scopes()):
        assert scope is not other
        for node, other_node in zip(scope.nodes, other.nodes):
            assert node is not other_node
            with pytest.raises(FrozenInstanceError):
                node.name = 'changed'
            assert isinstance(node.deps, tuple)

    for record in records:
        record.defines.clear()
        for item in record.nodes:
            item.raw_deps.clear()
            item.deps.clear()
            item.predicates.clear()
            item.name = 'changed'
        record.nodes.clear()

    assert to_dict(first) == expected
    assert to_dict(second) == expected


def test_builtin_bindings_are_resolved_and_marked_outside_the_source_ir():
    records = build_ir(ast.parse('def main():\n    print(1)\n'))

    resolve(records)

    builtin_scope = next(scope for scope in records if scope.kind == 'builtins')
    builtin_binding = builtin_scope.bindings['print'][0]
    assert not hasattr(builtin_binding, 'is_builtin')
    resolve_read_occurrences(records)
    graph = lower(records)
    builtin_scope = next(scope for scope in graph.walk_scopes() if scope.kind == 'builtins')
    builtin_node = next(node for node in builtin_scope.nodes if node.name == 'print')
    call = next(node for scope in graph.walk_scopes() for node in scope.nodes if node.kind is NodeKind.CALL)
    main = graph.children[0].children[0]

    assert main is not None
    assert builtin_node.is_builtin
    assert builtin_node in call.deps
    measured = profile(main)
    assert measured.variable__builtin__read__count == 1
    assert measured.variable__module__read__count == 0
    assert measured.variable__unresolved__read__count == 0
    assert measured.call__occurrences__resolved__count == 1


def test_source_binding_shadows_a_builtin_binding():
    records = build_ir(ast.parse('def main(print):\n    print()\n'))

    resolve(records)

    assert all(scope.kind != 'builtins' for scope in records)
    resolve_read_occurrences(records)
    graph = lower(records)
    call = next(node for scope in graph.walk_scopes() for node in scope.nodes if node.kind is NodeKind.CALL)

    assert any(
        dependency.name == 'print' for dependency in call.deps
    )


def test_lowering_resolves_parent_scopes_independent_of_record_order():
    records = build_ir(ast.parse(
        'def outer():\n'
        '    def inner():\n'
        '        return 1\n'
        '    return inner()\n'
    ))

    resolve_read_occurrences(records)
    lowered = lower(list(reversed(records)))
    scopes_by_record = dict(zip(records, lowered.walk_scopes()))

    assert lowered.kind == 'root'
    assert to_dict(lowered) == to_dict(lower(records))
    for record, scope in scopes_by_record.items():
        if record.parent is None:
            assert scope.parent is None
        else:
            assert scope.parent is scopes_by_record[record.parent]


@pytest.mark.parametrize(
    'fixture',
    [
        'expressions',
        'external_aliases',
        'recursive_flows',
        'repeated_definition_cleanup',
        'qualified_inherited_call',
        'repeated_comprehension_walrus',
    ],
)
def test_descriptions_do_not_affect_resolution_or_metrics(fixture):
    source = (FIXTURES / fixture / 'input.py').read_text()
    original = build_ir(ast.parse(source))
    renamed = build_ir(ast.parse(source))
    for scope in renamed:
        scope.name = 'same scope description'
        for node in scope.nodes:
            node.name = 'same node description'

    for records in (original, renamed):
        resolve(records)
        remove_resolved_scope_bindings(records)
        resolve_read_occurrences(records)
    original_graph = lower(original)
    renamed_graph = lower(renamed)

    assert _describe_topology(original_graph) == _describe_topology(renamed_graph)
    assert (
        summarize(original_graph, depth=0)['scopes'][0]['profile']
        == summarize(renamed_graph, depth=0)['scopes'][0]['profile']
    )
    original_profiles = walk_scope_tree(summarize(original_graph, include_own_profile=True)['scopes'])
    renamed_profiles = walk_scope_tree(summarize(renamed_graph, include_own_profile=True)['scopes'])
    assert [scope['own_profile'] for scope in original_profiles] == [
        scope['own_profile'] for scope in renamed_profiles
    ]


@pytest.mark.parametrize(
    'fixture', ['internal_calls', 'class_calls', 'shadowed_imports']
)
def test_package_resolution_ignores_descriptions(monkeypatch, fixture):
    root = FIXTURES.parent / 'package' / fixture
    original = package_builder.build_package(root)

    def build_renamed_ir(tree, **kwargs):
        records = build_ir(tree, **kwargs)
        for scope in records:
            scope.name = 'same description'
            for node in scope.nodes:
                node.name = 'same description'
        return records

    monkeypatch.setattr(package_builder, 'build_ir', build_renamed_ir)
    renamed = package_builder.build_package(root)

    assert _describe_topology(original) == _describe_topology(renamed)
    assert (
        summarize(original, depth=0)['scopes'][0]['profile']
        == summarize(renamed, depth=0)['scopes'][0]['profile']
    )


def _describe_topology(root):
    scopes = list(root.walk_scopes())
    identities = {}
    for index, scope in enumerate(scopes):
        identities[id(scope)] = (index, None)
        for position, node in enumerate(scope.nodes):
            identities[id(node)] = (index, position)
    return [
        (identities[id(node)], tuple(identities[id(dep)] for dep in node.deps))
        for scope in scopes
        for node in scope.nodes
    ]
