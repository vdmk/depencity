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
    assert first_stats.expression_paths == 0
    assert first_stats.count == 0
    assert first_stats.depth_distribution == {}


def test_measure_restarts_paths_after_omitting_a_cycle():
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
    assert stats.count == 2
    assert stats.depth_distribution == {0: 1, 1: 1}
    assert stats.depth_max == 1


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
    assert profile.graph__paths__expressions__count == 1
    assert profile.graph__paths__data__count_sum == 2
    assert profile.graph__paths__data__length__distribution == {0: 1, 1: 1}
    assert profile.graph__paths__data__length__max == 1


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
