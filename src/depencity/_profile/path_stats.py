"""Statistics for expression paths and local data-dependency chains.

Expression paths end at graph sinks. Data chains end at named nodes, whether
or not later nodes consume them. Control flow is not modeled here; conditions
are ordinary data dependencies.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import TYPE_CHECKING

from depencity._graph.model.enums import NodeKind
from depencity._profile.model.data_paths_stats import DataPathsStats

if TYPE_CHECKING:
    from depencity._graph.model.node import Node
    from depencity._graph.model.scope import Scope


def summarize_distribution(distribution: dict[int, int]) -> tuple[int, float, int, int]:
    """Return count, mean, maximum, and nearest-rank p95 for chain depths."""
    count = sum(distribution.values())
    weighted_depth = sum(
        depth * occurrences for depth, occurrences in distribution.items()
    )
    maximum = max(distribution, default=0)
    if not count:
        return 0, 0.0, 0, 0

    mean = weighted_depth / count
    rank = (95 * count + 99) // 100
    seen = 0
    # The guard makes an empty loop impossible; exclude that edge from coverage.
    for depth in sorted(distribution):  # pragma: no branch
        seen += distribution[depth]
        if seen >= rank:
            break
    return count, mean, maximum, depth


def measure(scope: Scope) -> DataPathsStats:
    """Measure sink expression paths and paths ending at named nodes."""
    return measure_nodes(scope.nodes, [scope])


def measure_nodes(nodes: list[Node], scopes: list[Scope] | None = None) -> DataPathsStats:
    """Measure paths across an explicit subgraph node set."""
    all_nodes = [node for node in nodes if node.kind is not NodeKind.BINDING]
    scope_ids = {id(scope) for scope in scopes or ()}
    named_nodes = [
        node
        for node in all_nodes
        if node.is_named_endpoint
    ]
    expression_stats, named_stats = _compute(all_nodes, named_nodes, scope_ids)
    return replace(
        named_stats,
        expression_paths=expression_stats.count,
        expression_depth_max=expression_stats.depth_max,
    )


def _compute(
    nodes: list[Node], named_nodes: list[Node], scope_ids: set[int]
) -> tuple[DataPathsStats, DataPathsStats]:
    node_ids = {id(node) for node in nodes}
    cyclic_ids = {
        node_id
        for component in _cyclic_components(nodes)
        for node_id in component
    }
    measured_ids = node_ids | scope_ids
    dependencies: dict[int, list[Node | Scope]] = {}
    depended_by: set[int] = set()

    for node in nodes:
        if id(node) in cyclic_ids:
            continue
        in_scope: list[Node | Scope] = []
        for dependency in node.deps:
            dependency_id = id(dependency)
            if dependency_id not in measured_ids or dependency_id in cyclic_ids:
                continue
            in_scope.append(dependency)
            depended_by.add(dependency_id)
        dependencies[id(node)] = in_scope

    computed: dict[int, dict[int, int]] = {
        scope_id: {0: 1} for scope_id in scope_ids
    }

    def compute(node: Node) -> dict[int, int]:
        root_id = id(node)
        pending: list[tuple[Node | Scope, bool]] = [(node, False)]
        while pending:
            current, dependencies_ready = pending.pop()
            current_id = id(current)
            if current_id in computed:
                continue
            if not dependencies_ready:
                pending.append((current, True))
                pending.extend(
                    (dependency, False)
                    for dependency in dependencies[current_id]
                    if id(dependency) not in computed
                )
                continue

            distribution: Counter[int] = Counter()
            for dependency in dependencies[current_id]:
                for depth, count in computed[id(dependency)].items():
                    distribution[depth + 1] += count
            if not distribution:
                distribution[0] = 1
            computed[current_id] = distribution
        return computed[root_id]

    distribution: Counter[int] = Counter()
    named_distribution: Counter[int] = Counter()
    named_node_ids = {id(node) for node in named_nodes}
    for node in nodes:
        node_id = id(node)
        if node_id in cyclic_ids:
            continue
        node_distribution = compute(node)
        if node_id not in depended_by:
            distribution.update(node_distribution)
        if node_id in named_node_ids:
            named_distribution.update(node_distribution)
    expression_count, expression_mean, expression_maximum, expression_p95 = (
        summarize_distribution(distribution)
    )
    named_count, named_mean, named_maximum, named_p95 = summarize_distribution(
        named_distribution
    )
    return (
        DataPathsStats(
            count=expression_count,
            depth_max=expression_maximum,
            depth_mean=expression_mean,
            depth_p95=expression_p95,
            depth_distribution=dict(distribution),
        ),
        DataPathsStats(
            count=named_count,
            depth_max=named_maximum,
            depth_mean=named_mean,
            depth_p95=named_p95,
            depth_distribution=dict(named_distribution),
        ),
    )


def _cyclic_components(nodes: list[Node]) -> list[list[int]]:
    """Return cyclic strongly connected components as node identities."""
    node_ids = {id(node) for node in nodes}
    adjacency = {
        id(node): [
            id(dependency)
            for dependency in node.deps
            if id(dependency) in node_ids
        ]
        for node in nodes
    }
    reverse_adjacency: dict[int, list[int]] = {node_id: [] for node_id in node_ids}
    for node_id, dependencies in adjacency.items():
        for dependency_id in dependencies:
            reverse_adjacency[dependency_id].append(node_id)

    visited: set[int] = set()
    finish_order: list[int] = []
    for node in nodes:
        root_id = id(node)
        if root_id in visited:
            continue
        visited.add(root_id)
        pending = [(root_id, 0)]
        while pending:
            node_id, dependency_index = pending[-1]
            dependencies = adjacency[node_id]
            if dependency_index == len(dependencies):
                finish_order.append(node_id)
                pending.pop()
                continue

            dependency_id = dependencies[dependency_index]
            pending[-1] = (node_id, dependency_index + 1)
            if dependency_id not in visited:
                visited.add(dependency_id)
                pending.append((dependency_id, 0))

    cyclic_components = []
    visited.clear()
    for root_id in reversed(finish_order):
        if root_id in visited:
            continue
        component = []
        component_pending = [root_id]
        visited.add(root_id)
        while component_pending:
            node_id = component_pending.pop()
            component.append(node_id)
            for predecessor_id in reverse_adjacency[node_id]:
                if predecessor_id not in visited:
                    visited.add(predecessor_id)
                    component_pending.append(predecessor_id)
        if len(component) > 1 or root_id in adjacency[root_id]:
            cyclic_components.append(component)
    return cyclic_components
