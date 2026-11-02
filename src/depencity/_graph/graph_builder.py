import ast
from typing import cast

from depencity._graph.ir_builder import build_resolved_ir
from depencity._graph.model.enums import (
    EdgeType,
    NodeKind,
    OutputType,
    ScopeKind,
)
from depencity._graph.model.ir import NodeRecord, ScopeRecord
from depencity._graph.model.node import DependencyEdge, Node
from depencity._graph.model.scope import Scope


def build(source: str) -> Scope:
    """Build and resolve a dependency graph from Python source text."""
    return lower(build_resolved_ir(ast.parse(source)))


def lower(records: list[ScopeRecord]) -> Scope:
    """Return a detached graph root from completed IR without modifying the IR.

    Scope containers and the identity table are private until construction ends.
    Edges are wired after all nodes exist so cyclic endpoints can be linked.
    No mutable IR collection is shared with the resulting graph.
    """
    scope_bindings = {
        bound_scope: binding
        for record in records
        for binding in record.nodes
        for bound_scope in binding.bound_scopes
    }
    scopes = {}
    for record in records:
        scopes[id(record)] = Scope(
            name=record.name,
            kind=record.kind,
            parent=None,
            is_standalone_module=record.is_standalone_module,
        )
    for record in records:
        if record.parent is not None:
            scopes[id(record)].parent = scopes[id(record.parent)]
    entities: dict[int, Node | Scope] = dict(scopes)
    for record in records:
        for item in record.nodes:
            entities[id(item)] = Node(
                name=item.name,
                scope=scopes[id(record)],
                display_name=_create_display_name(item, record),
                kind=item.kind,
                operation_type=item.operation_type,
                access=item.access,
                is_instance_attribute=item.is_instance_attribute,
                is_class_attribute=item.is_class_attribute,
                is_global_write=item.is_global_write,
                is_nonlocal_write=item.is_nonlocal_write,
                is_named_endpoint=(
                    item.binding is not None
                    or item.output_type == OutputType.RETURN
                    or (
                        item.output_type == OutputType.RESULT
                        and record.kind == ScopeKind.COMPREHENSION
                    )
                ),
                is_version_merge=_has_version_merge(item, scope_bindings),
                is_generator_expression=item.is_generator_expression,
                is_import=item.is_import,
                is_unresolved=item.is_unresolved,
                output_type=item.output_type,
            )
    # Nodes stay private until their edges, including cycles, have been wired.
    for record in records:
        for item in record.nodes:
            object.__setattr__(
                entities[id(item)], 'dependency_edges',
                _create_dependency_edges(
                    item,
                    id(item.declared_scope) if id(item.declared_scope) in scopes else None,
                    entities,
                ),
            )
    for record in records:
        scope = scopes[id(record)]
        scope.children = [scopes[id(child)] for child in record.children]
        scope.nodes = [cast(Node, entities[id(item)]) for item in record.nodes]
    return next(scope for scope in scopes.values() if scope.parent is None)


def _has_version_merge(
    item: NodeRecord, scope_bindings: dict[ScopeRecord, NodeRecord],
) -> bool:
    seen_bindings: dict[int | tuple[int, str], NodeRecord | ScopeRecord] = {}
    dependencies = dict.fromkeys(item.deps)
    for targets in item.read_targets.values():
        dependencies.update(dict.fromkeys(targets))
    for dependency in dependencies:
        key: int | tuple[int, str]
        version: NodeRecord | ScopeRecord
        if isinstance(dependency, ScopeRecord):
            binding = scope_bindings.get(dependency)
            if binding is None:
                continue
            key = id(binding)
            version = dependency
        else:
            if dependency.binding is None or dependency.is_unresolved:
                continue
            key = (
                id(dependency.binding_node)
                if dependency.binding_node is not None
                else (id(dependency.scope), dependency.binding)
            )
            version = dependency.declared_scope or dependency
        if key in seen_bindings and seen_bindings[key] is not version:
            return True
        seen_bindings[key] = version
    return False


def _create_dependency_edges(
    item: NodeRecord,
    declared_scope_id: int | None,
    entities: dict[int, Node | Scope],
) -> tuple[DependencyEdge, ...]:
    edges = {}
    read_targets = item.read_targets
    for dependency, inputs in item.deps.items():
        occurrences = inputs.values()
        accesses = {access for access in occurrences if access is not None}
        if len(accesses) > 1:
            raise ValueError('A dependency edge contains conflicting access qualifiers')
        access = next(iter(accesses), None)
        # Directly resolved dependencies still contribute one occurrence without
        # expression inputs. Other relationship types have independent counts.
        count = len(occurrences) or 1
        is_call_argument = _is_call_argument_dependency(item, dependency)
        is_structural = bool(inputs) and all(
            occurrence is not None and occurrence.is_structural
            for occurrence in inputs
        )
        is_predicate = dependency in item.predicates
        if is_structural:
            edge_type = EdgeType.ITERATION
        elif is_predicate:
            edge_type = EdgeType.PREDICATE
        else:
            edge_type = EdgeType.DATA
        edge = DependencyEdge(
            entities[id(dependency)], count, access,
            edge_type=edge_type,
            is_call_argument=is_call_argument,
            is_callee=(
                not is_structural
                and _is_callee_dependency(item, dependency, is_call_argument)
            ),
            is_variable_read=(
                (
                    dependency.kind is NodeKind.VARIABLE
                    or (isinstance(dependency, ScopeRecord) and isinstance(dependency.symbol, str))
                    or (isinstance(dependency, NodeRecord) and dependency.is_unresolved)
                )
                and any(dependency in targets for targets in read_targets.values())
            ),
            is_callable_read=(
                isinstance(dependency, NodeRecord)
                and dependency.output_type is not None
                and dependency.scope not in item.deps
                and any(dependency.scope in targets for targets in read_targets.values())
            ),
        )
        edges[id(dependency), edge_type] = edge
        if is_structural and is_predicate:
            edges[id(dependency), EdgeType.PREDICATE] = edge._replace(
                edge_type=EdgeType.PREDICATE,
            )
    for targets in read_targets.values():
        dependency = targets[0]
        is_unresolved = isinstance(dependency, NodeRecord) and dependency.is_unresolved
        is_variable = (
            dependency.kind is NodeKind.VARIABLE
            or (isinstance(dependency, ScopeRecord) and isinstance(dependency.symbol, str))
        )
        if not is_unresolved and not is_variable:
            if not isinstance(dependency, ScopeRecord) or dependency in item.deps:
                continue
        is_callable_read = dependency not in item.deps and isinstance(dependency, ScopeRecord)
        if is_callable_read:
            dependency = next(
                candidate for candidate in item.deps
                if isinstance(candidate, NodeRecord)
                and candidate.output_type is not None
                and candidate.scope is dependency
            )
        key = (id(dependency), EdgeType.DATA)
        edge = edges[key]
        if is_callable_read:
            edges[key] = edge._replace(
                is_callable_read=True,
                callable_read_count=edge.callable_read_count + 1,
            )
        else:
            edges[key] = edge._replace(
                is_variable_read=True,
                read_contribution_count=edge.read_contribution_count + 1,
            )
    if item.binding_node is not None:
        edges[id(item.binding_node), EdgeType.BINDING] = DependencyEdge(
            entities[id(item.binding_node)], 1, None, edge_type=EdgeType.BINDING,
        )
    for scope in item.bound_scopes:
        edges[id(scope), EdgeType.BINDING] = DependencyEdge(
            entities[id(scope)], 1, None, edge_type=EdgeType.BINDING,
        )
    if item.scope.kind == ScopeKind.ROOT:
        for class_scope in item.class_object_targets | item.callable_targets:
            if class_scope not in item.deps:
                edges[id(class_scope), EdgeType.DECLARATION] = DependencyEdge(
                    entities[id(class_scope)], 1, None, edge_type=EdgeType.DECLARATION,
                )
    if declared_scope_id is not None:
        edges[declared_scope_id, EdgeType.DECLARATION] = DependencyEdge(
            entities[declared_scope_id], 1, None, edge_type=EdgeType.DECLARATION,
        )
    return tuple(edges.values())


def _is_callee_dependency(
    item: NodeRecord,
    dependency: NodeRecord | ScopeRecord,
    is_call_argument: bool,
) -> bool:
    if not item.raw_calls:
        return False
    if any(
        occurrence is not None and occurrence.is_callee
        and occurrence not in item.inputs
        for occurrence in item.deps[dependency]
    ):
        return True
    if isinstance(dependency, ScopeRecord) and None in item.deps[dependency] and (
        dependency in item.resolved_call_targets
        or dependency in item.resolved_class_targets
    ):
        return True
    if any(
        occurrence.is_callee and dependency in targets
        for occurrence, targets in item.read_targets.items()
    ):
        return True
    if is_call_argument:
        return False
    if isinstance(dependency, ScopeRecord):
        return True
    if dependency.scope.kind == ScopeKind.ROOT:
        return True
    if dependency.output_type is not None:
        return dependency.scope in item.resolved_call_targets
    if dependency.is_unresolved:
        return dependency.binding in item.raw_calls and (
            not item.deps[dependency] or None in item.deps[dependency]
        )
    return False


def _is_call_argument_dependency(
    item: NodeRecord, dependency: NodeRecord | ScopeRecord,
) -> bool:
    if item.kind != NodeKind.CALL:
        return False
    return any(
        occurrence.is_call_argument and dependency in targets
        for occurrence, targets in item.read_targets.items()
    )


def _create_display_name(item: NodeRecord, scope_record: ScopeRecord) -> str:
    if item.display_name is not None:
        return item.display_name
    if item.kind is NodeKind.CALL and item.raw_calls:
        return f'{item.raw_calls[0]}()'
    if item.output_type is OutputType.RETURN:
        returns = [
            node
            for node in scope_record.nodes
            if node.output_type is OutputType.RETURN
        ]
        version = next(
            index for index, output in enumerate(returns, start=1)
            if output is item
        )
        return f'return ({version})'
    if item.binding is None:
        return item.name
    binding_scope = scope_record
    if item.binding in scope_record.global_decls:
        parent = scope_record.parent
        while parent is not None and parent.kind != ScopeKind.MODULE:
            parent = parent.parent
        if parent is not None:
            binding_scope = parent
    definitions = binding_scope.bindings.get(item.binding, ())
    if item not in definitions:
        definitions = scope_record.bindings.get(item.binding, ())
    if len(definitions) < 2:
        return item.binding
    version = next(
        index for index, definition in enumerate(definitions, start=1)
        if definition is item
    )
    return f'{item.binding} v{version}'
