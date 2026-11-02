import json

from depencity._graph.model.node import Node
from depencity._graph.model.scope import Scope, create_scope_ids, create_unique_id
from depencity._version import __version__


def to_dict(root: Scope) -> dict:
    scopes = list(root.walk_scopes())
    scope_ids = create_scope_ids(scopes)
    used_ids = set(scope_ids.values())
    node_ids = {}
    for scope in scopes:
        for index, node in enumerate(scope.nodes):
            candidate = f'{scope_ids[id(scope)]}.{node.name}#{index}'
            node_id = create_unique_id(candidate, used_ids)
            node_ids[id(node)] = node_id
            used_ids.add(node_id)
    return {
        'version': __version__,
        'scopes': [
            _scope_dict(scope, scope_ids, node_ids)
            for scope in scopes
        ],
        'nodes': [
            _node_dict(node, scope_ids, node_ids)
            for scope in scopes
            for node in scope.nodes
        ],
        'edges': sorted([
            {
                'source': _dependency_id(
                    edge.dependency, scope_ids, node_ids
                ),
                'target': node_ids[id(node)],
                'count': edge.count,
                'access': edge.access.value if edge.access is not None else None,
                'is_call_argument': edge.is_call_argument,
                'is_callee': edge.is_callee,
                'is_variable_read': edge.is_variable_read,
                'is_callable_read': edge.is_callable_read,
                'read_contribution_count': edge.read_contribution_count,
                'callable_read_count': edge.callable_read_count,
                'edge_type': edge.edge_type.value,
            }
            for scope in scopes
            for node in scope.nodes
            for edge in node.dependency_edges
        ], key=lambda edge: (
            edge['source'], edge['target'], json.dumps(edge, sort_keys=True)
        )),
    }


def to_json(root: Scope) -> str:
    return json.dumps(to_dict(root), indent=2, sort_keys=True)


def _scope_dict(
    scope: Scope,
    scope_ids: dict[int, str],
    node_ids: dict[int, str],
) -> dict:
    result = {
        'id': scope_ids[id(scope)],
        'name': scope.name,
        'kind': scope.kind.value,
        'parent': scope_ids.get(id(scope.parent)),
        'children': [scope_ids[id(child)] for child in scope.children],
        'nodes': [node_ids[id(node)] for node in scope.nodes],
    }
    return result


def _node_dict(
    node: Node,
    scope_ids: dict[int, str],
    node_ids: dict[int, str],
) -> dict:
    result = {
        'id': node_ids[id(node)],
        'name': node.name,
        'display_name': node.display_name,
        'scope': scope_ids[id(node.scope)],
        'kind': node.kind.value,
        'access': node.access.value if node.access else None,
        'is_instance_attribute': node.is_instance_attribute,
        'is_class_attribute': node.is_class_attribute,
        'is_global_write': node.is_global_write,
        'is_nonlocal_write': node.is_nonlocal_write,
        'dependencies': sorted(
            _dependency_id(dependency, scope_ids, node_ids)
            for dependency in node.deps
        ),
    }
    if node.is_builtin:
        result['is_builtin'] = True
    if node.is_unresolved:
        result['is_unresolved'] = True
    if node.operation_type is not None:
        result['operation_type'] = node.operation_type.value
    return result


def _dependency_id(
    dependency: Node | Scope,
    scope_ids: dict[int, str],
    node_ids: dict[int, str],
) -> str:
    return (
        node_ids[id(dependency)]
        if isinstance(dependency, Node)
        else scope_ids[id(dependency)]
    )
