from __future__ import annotations

from typing import Any

from depencity._graph.model.enums import (
    AccessMode,
    EdgeType,
    NodeKind,
    OperationType,
    ScopeKind,
)
from depencity._graph.model.node import Node
from depencity._graph.model.scope import Scope
from depencity._profile.model.scope_profile import ScopeProfile
from depencity._profile.path_stats import (
    _cyclic_components,
    measure_nodes,
)

type VariableReadIdentity = tuple[str, int, int]


def count_cyclic_components(scopes: list[Scope]) -> int:
    nodes = [node for scope in scopes for node in scope.nodes]
    return len(_cyclic_components(nodes))


def profile(
    scope: Scope, *, include_paths: bool = True, include_cycles: bool = True,
    scope_metrics: dict[int, dict] | None = None,
) -> ScopeProfile:
    """Calculate fresh scope metrics without storing analysis on the graph."""
    return _measure_scopes(
        [scope], scope_metrics, include_paths=include_paths, include_cycles=include_cycles
    )


def profile_subgraph(
    root: Scope, scope_metrics: dict[int, dict] | None = None,
    *, include_paths: bool = True, include_cycles: bool = True,
) -> ScopeProfile:
    """Profile a subtree, caching only metrics that combine across scopes."""
    return _measure_scopes(
        list(root.walk_scopes()), scope_metrics,
        include_paths=include_paths, include_cycles=include_cycles,
    )


def _measure_scopes(
    scopes: list[Scope], scope_metrics: dict[int, dict] | None,
    *, include_paths: bool, include_cycles: bool,
) -> ScopeProfile:
    if scope_metrics is None:
        scope_metrics = {}
    for scope in scopes:
        if id(scope) not in scope_metrics:
            scope_metrics[id(scope)] = _measure_scope_metrics(scope)

    combined: dict[str, Any] = {}
    variable_reads: set[VariableReadIdentity] = set()
    external_targets: set[int] = set()
    for scope in scopes:
        for name, value in scope_metrics[id(scope)].items():
            if name == 'variables_read_distinct':
                variable_reads.update(value)
            elif name == 'external_call_targets':
                external_targets.update(value)
            else:
                combined[name] = combined.get(name, 0) + value
    combined['variable__total__read__distinct_count'] = len(variable_reads)
    combined['call__dependencies__external__distinct_count'] = len(external_targets)
    result = ScopeProfile(**combined)

    if include_paths:
        paths = measure_nodes(
            [node for scope in scopes for node in scope.nodes], scopes
        )
        result.graph__paths__expressions__count = paths.expression_paths
        result.graph__paths__expressions__length__max = paths.expression_depth_max
        result.graph__paths__data__count_sum = paths.count
        result.graph__paths__data__length__max = paths.depth_max
        result.graph__paths__data__length__mean = paths.depth_mean
        result.graph__paths__data__length__p95 = paths.depth_p95
        result.graph__paths__data__length__distribution = paths.depth_distribution
    if include_cycles:
        components = _cyclic_components([node for scope in scopes for node in scope.nodes])
        result.graph__cyclic_components__count = len(components)
        result.graph__cyclic_components__nodes__count = sum(map(len, components))
    return result


def _measure_scope_metrics(scope: Scope) -> dict:
    """Measure counters and identities that combine across scopes."""
    enclosing_depths = {}
    enclosing_scope = scope.parent
    depth = 1
    while enclosing_scope is not None and enclosing_scope.kind not in (ScopeKind.MODULE, ScopeKind.ROOT):
        enclosing_depths[id(enclosing_scope)] = depth
        depth += 1
        enclosing_scope = enclosing_scope.parent

    result = ScopeProfile()
    _measure_references(scope, result)
    identities = _measure_metric_contract(scope, result, enclosing_depths)
    return {
        name: value for name, value in vars(result).items()
        if not name.startswith('graph__paths__') and not name.startswith('graph__cyclic_components__')
    } | identities


def _measure_metric_contract(
    scope: Scope,
    result: ScopeProfile,
    enclosing_depths: dict[int, int],
) -> dict:
    """Measure variable occurrences independently from graph edge deduplication."""
    variables_read_distinct: set[VariableReadIdentity] = set()
    external_call_targets: set[int] = set()
    for node in scope.nodes:
        result.graph__version_merges__count += node.is_version_merge
        if node.kind == NodeKind.REFERENCE:
            if node.access == AccessMode.READ:
                result.attribute__total__read__count += 1
            elif node.access == AccessMode.WRITE:
                result.attribute__total__write__count += 1
            else:
                raise ValueError('reference node has invalid access mode')
        elif node.kind == NodeKind.SUBSCRIPT:
            if node.access == AccessMode.READ:
                result.subscript__read__count += 1
            elif node.access == AccessMode.WRITE:
                result.subscript__write__count += 1
            else:
                raise ValueError('subscript node has invalid access mode')

        resolved_targets, external_targets = node.collect_call_targets()
        if node.kind == NodeKind.CALL:
            result.call__occurrences__total__count += 1
            if resolved_targets:
                result.call__occurrences__resolved__count += 1
            else:
                result.call__occurrences__unresolved__count += 1
        result.call__dependencies__resolved_targets__count += len(resolved_targets)
        result.call__dependencies__external__count += len(external_targets)
        external_call_targets.update(
            id(target) for target in external_targets
        )

        if (
            node.access == AccessMode.WRITE
            and node.kind not in (NodeKind.REFERENCE, NodeKind.SUBSCRIPT)
            and not any(
                edge.edge_type is EdgeType.DECLARATION
                for edge in node.dependency_edges
            )
            and (
                node.kind is NodeKind.VARIABLE
                or (
                    node.operation_type == OperationType.MUTATION
                    and any(
                        edge.access == AccessMode.WRITE
                        for edge in node.dependency_edges
                    )
                )
            )
        ):
            _count_variable_write(result, node)

        for edge in node.dependency_edges:
            dependency = edge.dependency
            if edge.is_callable_read and edge.callable_read_count:
                assert isinstance(dependency, Node)
                _count_read(
                    scope, result, dependency.scope, enclosing_depths,
                    edge.callable_read_count, variables_read_distinct,
                )
            if (
                edge.edge_type is not EdgeType.DATA
                or not edge.is_variable_read
                or not edge.read_contribution_count
            ):
                continue
            if isinstance(dependency, Node) and dependency.is_unresolved:
                result.variable__unresolved__read__count += edge.read_contribution_count
                variables_read_distinct.add(
                    ('unresolved', id(dependency.scope), id(dependency))
                )
            else:
                _count_read(
                    scope, result, dependency, enclosing_depths, edge.read_contribution_count,
                    variables_read_distinct,
                )

    result.variable__total__read__count = sum((
        result.variable__local__read__count,
        result.variable__enclosing__read__count,
        result.variable__module__read__count,
        result.variable__builtin__read__count,
        result.variable__other_scope__read__count,
        result.variable__unresolved__read__count,
    ))
    result.variable__total__write__count = sum((
        result.variable__local__write__count,
        result.variable__enclosing__write__count,
        result.variable__module__write__count,
    ))
    return {
        'variables_read_distinct': variables_read_distinct,
        'external_call_targets': external_call_targets,
    }


def _count_read(
    scope: Scope,
    result: ScopeProfile,
    dependency: Node | Scope,
    enclosing_depths: dict[int, int],
    count: int,
    variables_read_distinct: set[VariableReadIdentity],
) -> None:
    binding = _find_read_binding(dependency)
    is_builtin = isinstance(dependency, Node) and dependency.is_builtin
    if isinstance(dependency, Scope):
        owner = dependency.parent
        identity = ('scope', id(owner), id(dependency))
    else:
        owner = dependency.scope
        identity = ('node', id(owner), id(dependency))
    if binding is not None:
        owner = binding.scope
        identity = ('builtin' if is_builtin else 'binding', id(owner), id(binding))

    if is_builtin:
        result.variable__builtin__read__count += count
    elif owner is scope:
        result.variable__local__read__count += count
    elif owner is None or owner.kind == ScopeKind.MODULE:
        result.variable__module__read__count += count
    elif id(owner) in enclosing_depths:
        result.variable__enclosing__read__count += count
    else:
        result.variable__other_scope__read__count += count
    variables_read_distinct.add(identity)


def _find_read_binding(dependency: Node | Scope) -> Node | None:
    if isinstance(dependency, Node):
        return next(
            (
                edge.dependency for edge in dependency.dependency_edges
                if edge.edge_type is EdgeType.BINDING
                and isinstance(edge.dependency, Node)
            ),
            None,
        )
    owner = dependency.parent
    while owner is not None:
        for candidate in owner.nodes:
            if candidate.kind is NodeKind.BINDING and any(
                edge.edge_type is EdgeType.BINDING and edge.dependency is dependency
                for edge in candidate.dependency_edges
            ):
                return candidate
        owner = owner.parent
    return None


def _count_variable_write(result: ScopeProfile, node: Node) -> None:
    if node.is_global_write:
        result.variable__module__write__count += 1
    elif node.is_nonlocal_write:
        result.variable__enclosing__write__count += 1
    else:
        result.variable__local__write__count += 1


def _measure_references(scope: Scope, result: ScopeProfile) -> None:
    for node in scope.nodes:
        if (
            (
                node.kind == NodeKind.COMPREHENSION
                and not node.is_generator_expression
            )
            or node.operation_type == OperationType.CONTAINER
        ):
            result.construction__container_creation__count += 1
        if node.kind != NodeKind.REFERENCE:
            continue
        own_state = node.is_instance_attribute or node.is_class_attribute
        if node.access == AccessMode.READ:
            if own_state:
                result.attribute__class__read__count += 1
            else:
                result.attribute__external__read__count += 1
        elif node.access == AccessMode.WRITE:
            if own_state:
                result.attribute__class__write__count += 1
            else:
                result.attribute__external__write__count += 1
