import ast

import pytest

from depencity._graph.graph_builder import lower
from depencity._graph.ir_builder import build_resolved_ir
from depencity._graph.model.enums import NodeKind, ScopeKind
from depencity._graph.model.node import Node
from depencity._graph.model.scope import Scope
from depencity._profile.classifier import profile_subgraph


@pytest.mark.parametrize('kind', [NodeKind.REFERENCE, NodeKind.SUBSCRIPT])
def test_profile_rejects_invalid_reference_access(kind):
    scope = Scope('f', ScopeKind.FUNCTION, None)
    scope.nodes = [Node('value', scope, display_name='value', kind=kind)]

    with pytest.raises(ValueError, match='invalid access mode'):
        profile_subgraph(scope)


def test_distinct_external_calls_use_import_identity_and_ignore_aliases():
    different_imports = _profile_source(
        '''
def first():
    import library_one as api
    return api.run()

def second():
    import library_two as api
    return api.run()
'''
    )
    same_import = _profile_source(
        '''
import library as a
import library as b

def main():
    a.run()
    b.run()
'''
    )

    assert different_imports.call__dependencies__external__distinct_count == 2
    assert same_import.call__dependencies__external__distinct_count == 1
    assert not any(isinstance(value, set) for value in vars(different_imports).values())
    assert not any(isinstance(value, set) for value in vars(same_import).values())


def _profile_source(source: str):
    records = build_resolved_ir(ast.parse(source))
    return profile_subgraph(lower(records))


