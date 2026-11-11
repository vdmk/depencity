import pytest

from depencity._graph.graph_builder import lower
from depencity._graph.model.enums import NodeKind, OutputType, ScopeKind
from depencity._graph.model.ir import NodeRecord, ScopeRecord
from depencity._profile.classifier import count_cyclic_components, profile_subgraph
from depencity._profile.path_stats import measure


def test_measure_handles_dependency_on_a_later_return_node():
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    call = NodeRecord('__call_f__', scope)
    returned = NodeRecord('__return_0__', scope)
    call.add_dependency(returned)
    scope.nodes = [call, returned]

    scope = lower([scope])
    stats = measure(scope)

    assert stats.expression_paths == 1
    assert stats.depth_max == 0


def test_measure_counts_branching_paths_with_expected_multiplicity():
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    seed = NodeRecord('seed', scope, binding='seed')
    left = NodeRecord('left', scope, binding='left')
    right = NodeRecord('right', scope, binding='right')
    joined = NodeRecord('joined', scope, binding='joined')
    returned = NodeRecord('__return_0__', scope, output_type=OutputType.RETURN)
    left.add_dependency(seed)
    right.add_dependency(seed)
    joined.add_dependency(left)
    joined.add_dependency(right)
    returned.add_dependency(joined)
    scope.nodes = [seed, left, right, joined, returned]

    stats = measure(lower([scope]))

    assert stats.expression_paths == 2
    assert stats.count == 7
    assert stats.depth_distribution == {0: 1, 1: 2, 2: 2, 3: 2}
    assert stats.depth_max == 3


def test_measure_handles_a_dependency_chain_longer_than_python_recursion_limit():
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    nodes = [
        NodeRecord(f'value_{index}', scope, binding=f'value_{index}')
        for index in range(1200)
    ]
    for previous, current in zip(nodes, nodes[1:]):
        current.add_dependency(previous)
    scope.nodes = nodes

    profile = profile_subgraph(lower([scope]))

    assert profile.graph__paths__data__count_sum == len(nodes)
    assert profile.graph__paths__data__length__max == len(nodes) - 1
    assert profile.graph__cyclic_components__count == 0
    assert profile.graph__cyclic_components__nodes__count == 0


def test_measure_handles_cycles_without_recursion_or_key_errors():
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    first = NodeRecord('first', scope)
    second = NodeRecord('second', scope)
    first.add_dependency(second)
    second.add_dependency(first)
    scope.nodes = [first, second]

    scope = lower([scope])
    first, second = scope.nodes
    first_stats = measure(scope)
    scope.nodes = [second, first]
    second_stats = measure(scope)

    assert first_stats == second_stats
    assert first_stats.expression_paths == 2
    assert first_stats.count == 0
    assert first_stats.depth_distribution == {}


def test_measure_preserves_paths_through_a_cycle():
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    first = NodeRecord('first', scope, binding='first')
    second = NodeRecord('second', scope, binding='second')
    downstream = NodeRecord('downstream', scope, binding='downstream')
    consumer = NodeRecord('consumer', scope, binding='consumer')
    first.add_dependency(second)
    second.add_dependency(first)
    downstream.add_dependency(second)
    consumer.add_dependency(downstream)
    scope.nodes = [first, second, downstream, consumer]

    stats = measure(lower([scope]))

    assert stats.expression_paths == 1
    assert stats.count == 4
    assert stats.depth_distribution == {2: 2, 3: 1, 4: 1}
    assert stats.depth_max == 4


def test_profile_measures_downstream_of_cross_scope_recursion():
    root = ScopeRecord('__root__', ScopeKind.ROOT)
    first_scope = ScopeRecord('first', ScopeKind.FUNCTION, root, symbol='first')
    second_scope = ScopeRecord('second', ScopeKind.FUNCTION, root, symbol='second')
    consumer_scope = ScopeRecord('consumer', ScopeKind.FUNCTION, root, symbol='consumer')
    root.children = [first_scope, second_scope, consumer_scope]

    call_second = NodeRecord('call_second', first_scope, kind=NodeKind.CALL)
    return_first = NodeRecord(
        'return_first', first_scope, output_type=OutputType.RETURN
    )
    call_first = NodeRecord('call_first', second_scope, kind=NodeKind.CALL)
    return_second = NodeRecord(
        'return_second', second_scope, output_type=OutputType.RETURN
    )
    call_second.add_dependency(return_second)
    return_first.add_dependency(call_second)
    call_first.add_dependency(return_first)
    return_second.add_dependency(call_first)
    first_scope.nodes = [call_second, return_first]
    second_scope.nodes = [call_first, return_second]

    after_cycle = NodeRecord(
        'after_cycle', consumer_scope, binding='after_cycle'
    )
    consumer = NodeRecord('consumer', consumer_scope, binding='consumer')
    after_cycle.add_dependency(return_first)
    consumer.add_dependency(after_cycle)
    consumer_scope.nodes = [after_cycle, consumer]

    graph = lower([root, first_scope, second_scope, consumer_scope])
    profile = profile_subgraph(graph)

    assert profile.graph__cyclic_components__count == 1
    assert profile.graph__cyclic_components__nodes__count == 4
    assert profile.graph__paths__expressions__count == 1
    assert profile.graph__paths__data__count_sum == 4
    assert profile.graph__paths__data__length__distribution == {4: 2, 5: 1, 6: 1}
    assert profile.graph__paths__data__length__max == 6


def test_count_cycles_is_stable_when_nodes_are_reordered():
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    first = NodeRecord('first', scope)
    second = NodeRecord('second', scope)
    third = NodeRecord('third', scope)
    first.add_dependency(second)
    second.add_dependency(third)
    third.add_dependency(first)

    scope.nodes = [first, second, third]
    scope = lower([scope])
    first, second, third = scope.nodes
    first_count = count_cyclic_components([scope])
    scope.nodes = [third, first, second]

    assert first_count == count_cyclic_components([scope]) == 1


def test_profile_subgraph_handles_empty_and_default_profiles():
    assert profile_subgraph(lower([ScopeRecord('__root__', ScopeKind.ROOT)])).graph__paths__expressions__count == 0

    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    scope.nodes = [NodeRecord('value', scope)]
    profile = profile_subgraph(lower([scope]))

    assert profile.graph__paths__expressions__count == 1


def test_measure_matches_first_repeat_enumeration_for_every_three_node_graph():
    """Independent route oracle covers loops, branching and component boundaries."""
    from collections import Counter
    from itertools import product

    for bits in product((False, True), repeat=9):
        adjacency = [{j for j in range(3) if bits[3 * i + j]} for i in range(3)]
        reachable = [set(deps) | {i} for i, deps in enumerate(adjacency)]
        for middle in range(3):
            for start in range(3):
                if middle in reachable[start]:
                    reachable[start].update(reachable[middle])
        groups = [{j for j in range(3) if j in reachable[i] and i in reachable[j]}
                  for i in range(3)]
        cyclic = [len(groups[i]) > 1 or i in adjacency[i] for i in range(3)]
        sinks = {i for i in range(3) if not any(i in deps for deps in adjacency)}
        sinks.update(i for i in range(3) if cyclic[i] and not any(
            adjacency[j] & groups[i] for j in range(3) if j not in groups[i]
        ))

        def enumerate_depths(node, visited):
            if node in visited or not adjacency[node]:
                return [0]
            return [1 + depth for dep in adjacency[node] for depth in enumerate_depths(
                dep, visited | {node}
            )]

        data = Counter()
        expressions = Counter()
        for i in range(3):
            depths = enumerate_depths(i, set())
            data.update(depths)
            if i in sinks:
                expressions.update(depths)
        for reverse in (False, True):
            scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
            nodes = [NodeRecord(str(i), scope, binding=str(i)) for i in range(3)]
            for i in range(3):
                for j in sorted(adjacency[i], reverse=reverse):
                    nodes[i].add_dependency(nodes[j])
            scope.nodes = list(reversed(nodes)) if reverse else nodes

            stats = measure(lower([scope]))

            assert stats.depth_distribution == dict(data), (bits, reverse)
            assert stats.expression_paths == expressions.total(), (bits, reverse)
            assert stats.expression_depth_max == max(expressions, default=0)


@pytest.mark.parametrize(('limit_name', 'limit', 'available'), (
    ('_MAX_CYCLIC_STATES', 1, False),
    ('_MAX_CYCLIC_STATES', 3, False),
    ('_MAX_CYCLIC_STATES', 4, True),
    ('_MAX_CYCLIC_WORK', 19, False),
    ('_MAX_CYCLIC_WORK', 20, True),
))
@pytest.mark.parametrize('named_cycle', (False, True))
def test_measure_reports_limits_without_partial_counts(
    monkeypatch, limit_name, limit, available, named_cycle,
):
    from depencity._profile import path_stats

    monkeypatch.setattr(path_stats, limit_name, limit)
    measured = []
    for reverse in (False, True):
        scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
        seed = NodeRecord('seed', scope, binding='seed')
        first = NodeRecord('first', scope, binding='first' if named_cycle else None)
        second = NodeRecord('second', scope, binding='second' if named_cycle else None)
        consumer = NodeRecord('consumer', scope, binding='consumer' if named_cycle else None)
        first_deps = [first, second, seed]
        second_deps = [first, second]
        for dep in reversed(first_deps) if reverse else first_deps:
            first.add_dependency(dep)
        for dep in reversed(second_deps) if reverse else second_deps:
            second.add_dependency(dep)
        consumer.add_dependency(first)
        nodes = [seed, first, second, consumer]
        scope.nodes = list(reversed(nodes)) if reverse else nodes

        stats = measure(lower([scope]))

        assert stats.expression_paths == (4 if available else None)
        assert stats.expression_depth_max == (3 if available else None)
        if named_cycle:
            assert stats.count == (13 if available else None)
            assert stats.depth_distribution == ({0: 1, 1: 3, 2: 7, 3: 2} if available else None)
            if not available:
                assert stats.depth_max is stats.depth_mean is stats.depth_p95 is None
        else:
            assert stats.count == 1
            assert stats.depth_distribution == {0: 1}
        measured.append(stats)
    assert measured[0] == measured[1]


def test_measure_propagates_unavailability_between_cyclic_components(monkeypatch):
    from depencity._profile import path_stats

    monkeypatch.setattr(path_stats, '_MAX_CYCLIC_STATES', 3)
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    first = NodeRecord('first', scope, binding='first')
    second = NodeRecord('second', scope, binding='second')
    consumer = NodeRecord('consumer', scope, binding='consumer')
    for node in (first, second):
        node.add_dependency(first)
        node.add_dependency(second)
    consumer.add_dependency(consumer)
    consumer.add_dependency(first)
    scope.nodes = [consumer, first, second]

    stats = measure(lower([scope]))

    assert stats.expression_paths is None
    assert stats.count is None
    assert stats.depth_distribution is None
