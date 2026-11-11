"""Statistics for expression paths and local data-dependency chains.

Expression paths end at sinks or members of terminal cyclic regions. Data chains
end at named nodes, whether or not later nodes consume them. Control flow is not
modeled here; conditions are ordinary data dependencies.
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


# Per cyclic component: bound exact state storage and dependency/bucket work.
# Exceeding either limit produces unavailable metrics, never partial counts.
_MAX_CYCLIC_STATES = 50_000
_MAX_CYCLIC_WORK = 1_000_000


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
    components = _cyclic_components(nodes)
    groups = {node_id: component for component in components for node_id in component}
    measured_ids = node_ids | scope_ids
    dependencies = {
        id(node): [id(dep) for dep in node.deps if id(dep) in measured_ids]
        for node in nodes
    }
    depended_by = {dep for deps in dependencies.values() for dep in deps}
    # A terminal cyclic region has no ordinary sink. Use every member as an
    # endpoint, without choosing an arbitrary representative or deleting edges.
    consumed_components = {
        id(groups[dep])
        for consumer, deps in dependencies.items() for dep in deps
        if dep in groups and groups.get(consumer) is not groups[dep]
    }
    terminal_cycle_ids = {
        node_id for component in components if id(component) not in consumed_components
        for node_id in component
    }
    computed: dict[int, dict[int, int] | None] = {
        scope_id: {0: 1} for scope_id in scope_ids
    }

    def compute(root_id: int) -> dict[int, int] | None:
        pending = [(root_id, False)]
        while pending:
            current_id, ready = pending.pop()
            if current_id in computed:
                continue
            group = groups.get(current_id, [current_id])
            members = set(group)
            if not ready:
                pending.append((current_id, True))
                pending.extend(
                    (dep, False) for member in group for dep in dependencies[member]
                    if dep not in members and dep not in computed
                )
                continue
            if current_id in groups:
                result = _compute_component(group, dependencies, computed)
                computed.update(result if result is not None else dict.fromkeys(group))
                continue
            distribution: Counter[int] = Counter()
            for dep in dependencies[current_id]:
                source = computed[dep]
                if source is None:
                    computed[current_id] = None
                    break
                for depth, count in source.items():
                    distribution[depth + 1] += count
            else:
                computed[current_id] = dict(distribution) or {0: 1}
        return computed[root_id]

    distribution: Counter[int] = Counter()
    named_distribution: Counter[int] = Counter()
    expression_unavailable = False
    named_unavailable = False
    named_node_ids = {id(node) for node in named_nodes}
    for node in nodes:
        node_id = id(node)
        node_distribution = compute(node_id)
        if node_id not in depended_by or node_id in terminal_cycle_ids:
            if node_distribution is None:
                expression_unavailable = True
            else:
                distribution.update(node_distribution)
        if node_id in named_node_ids:
            if node_distribution is None:
                named_unavailable = True
            else:
                named_distribution.update(node_distribution)
    results = []
    for depths, unavailable in (
        (distribution, expression_unavailable), (named_distribution, named_unavailable),
    ):
        if unavailable:
            results.append(DataPathsStats(
                count=None, depth_max=None, depth_mean=None, depth_p95=None,
                depth_distribution=None,
            ))
        else:
            count, mean, maximum, p95 = summarize_distribution(depths)
            results.append(DataPathsStats(
                count=count, depth_max=maximum, depth_mean=mean, depth_p95=p95,
                depth_distribution=dict(depths),
            ))
    return results[0], results[1]


def _compute_component(
    component: list[int], dependencies: dict[int, list[int]],
    computed: dict[int, dict[int, int] | None],
) -> dict[int, dict[int, int]] | None:
    """Count exact first-repeat paths with component-local visited-set states.

    Discover states by visited-set size, then evaluate deepest states first.
    Limits apply to the complete component, so availability is order independent.
    """
    if len(component) > _MAX_CYCLIC_STATES:
        return None
    bits = {node_id: 1 << index for index, node_id in enumerate(component)}
    if any(
        computed[dep] is None for member in component for dep in dependencies[member]
        if dep not in bits
    ):
        return None
    layer = {(member, bits[member]) for member in component}
    layers = []
    states = len(layer)
    work = 0
    while layer:
        if states > _MAX_CYCLIC_STATES:
            return None
        layers.append(layer)
        following = set()
        for member, visited in layer:
            work += len(dependencies[member])
            if work > _MAX_CYCLIC_WORK:
                return None
            for dep in dependencies[member]:
                if dep in bits and not visited & bits[dep]:
                    following.add((dep, visited | bits[dep]))
                    # Bound temporary storage as well as completed states.
                    if states + len(following) > _MAX_CYCLIC_STATES:
                        return None
        states += len(following)
        layer = following

    cache: dict[tuple[int, int], dict[int, int]] = {}
    for layer in reversed(layers):
        for member, visited in layer:
            distribution: Counter[int] = Counter()
            for dep in dependencies[member]:
                if dep in bits:
                    if visited & bits[dep]:
                        source = {0: 1}
                    else:
                        source = cache[(dep, visited | bits[dep])]
                else:
                    external_source = computed[dep]
                    assert external_source is not None
                    source = external_source
                work += len(source)
                if work > _MAX_CYCLIC_WORK:
                    return None
                for depth, count in source.items():
                    distribution[depth + 1] += count
            cache[(member, visited)] = dict(distribution)
    return {member: cache[(member, bits[member])] for member in component}


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
