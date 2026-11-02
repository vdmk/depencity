from __future__ import annotations

from depencity._graph.model.enums import EdgeType, NodeKind, OutputType, ScopeKind
from depencity._graph.model.node import Node
from depencity._graph.model.scope import Scope


def to_dot(root: Scope) -> str:
    scopes = list(root.walk_scopes())
    dot_ids: dict[int, str] = {}
    scope_binding_targets = {
        id(node): child
        for scope in scopes
        for child in scope.children
        for node in scope.nodes
        for edge in node.dependency_edges
        if edge.edge_type is EdgeType.DECLARATION and edge.dependency is child
    }
    for scope in scopes:
        dot_ids[id(scope)] = f'n{len(dot_ids)}'
        for node in scope.nodes:
            dot_ids[id(node)] = f'n{len(dot_ids)}'
    lines = ['digraph {', '  rankdir=LR;', '  compound=true;', '  node [fontname="monospace"];', '']
    edge_lines = []

    def _render_scope(scope: Scope, indent: str) -> None:
        sid = dot_ids[id(scope)]
        child_scopes = [child for child in scope.children if id(child) in dot_ids]
        lines.append(f'{indent}subgraph cluster_{sid} {{')
        lines.append(f'{indent}  label="{_escape_label(scope.name)}\\n({scope.kind.value})";')
        lines.append(f'{indent}  style=rounded;')
        lines.append(f'{indent}  {sid} [style=invis];')
        for node in scope.nodes:
            scope_target = scope_binding_targets.get(id(node))
            dst = dot_ids[id(scope_target or node)]
            if id(node) not in scope_binding_targets:
                lines.append(_render_node(node, dst, indent))
            rendered_dependencies = set()
            for edge in node.dependency_edges:
                if edge.edge_type is EdgeType.DECLARATION:
                    continue
                dep = edge.dependency
                scope_dependency = (
                    scope_binding_targets.get(id(dep), dep)
                    if isinstance(dep, Node)
                    else dep
                )
                if edge.edge_type.is_dependency:
                    if id(scope_dependency) in rendered_dependencies:
                        continue
                    rendered_dependencies.add(id(scope_dependency))
                source = dot_ids[id(scope_dependency)]
                tail = ''
                if isinstance(scope_dependency, Scope):
                    destination: Scope | None = scope_target or scope
                    while destination is not None and destination is not scope_dependency:
                        destination = destination.parent
                    if destination is None:
                        tail = f', ltail=cluster_{source}'
                if edge.edge_type is EdgeType.BINDING:
                    edge_lines.append(
                        f'  {source} -> {dst} '
                        f'[color=gray35 penwidth=2 style=dotted arrowhead=none constraint=false{tail}];'
                    )
                else:
                    edge_lines.append(f'  {source} -> {dst} [color=steelblue{tail}];')
        for child in child_scopes:
            lines.append('')
            _render_scope(child, indent + '  ')
        lines.append(f'{indent}}}')
        lines.append('')

    _render_scope(root, '  ')

    lines.extend(sorted(edge_lines))
    lines.append('}')
    return '\n'.join(lines)


def _render_node(
    node: Node,
    dot_id: str,
    indent: str,
) -> str:
    label = _escape_label(node.display_name)
    attributes = ''
    if node.kind is NodeKind.BINDING:
        attributes = ' shape=box style="rounded,filled" fillcolor=lightyellow'
    elif node.kind is NodeKind.CONDITION:
        attributes = ' shape=diamond'
    elif node.kind is NodeKind.CALL:
        attributes = ' shape=box style=filled fillcolor=lightcyan'
    elif node.kind is NodeKind.OPERATION or (
        node.output_type is OutputType.RESULT
        and node.scope.kind == ScopeKind.COMPREHENSION
    ):
        attributes = ' shape=box'
    return f'{indent}  {dot_id} [label="{label}"{attributes}];'


def _escape_label(label: str) -> str:
    return (
        label.replace('\\', '\\\\')
        .replace('"', '\\"')
        .replace('\n', '\\n')
        .replace('\r', '\\r')
    )
