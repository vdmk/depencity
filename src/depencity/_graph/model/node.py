from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple

from depencity._graph.model.enums import (
    AccessMode,
    EdgeType,
    NodeKind,
    OperationType,
    OutputType,
    ScopeKind,
)

if TYPE_CHECKING:
    from depencity._graph.model.scope import Scope


class DependencyEdge(NamedTuple):
    """One typed relationship with its qualifiers and occurrence count.

    ``count`` counts all relationship occurrences, independently of ``access``.
    ``edge_type`` selects data, iteration, predicate, binding, or declaration
    relationships.
    Each endpoint pair has at most one edge per type. Binding and declaration
    edges count one occurrence; dependency edges retain source multiplicity.
    Dependency metrics and traversal select data, iteration, and predicate
    relationships, visiting each dependency endpoint once across those types.
    An unqualified structural edge has ``access=None`` and a positive count.
    ``is_call_argument`` identifies argument uses independently of ``is_callee``;
    a shared endpoint can supply both roles.
    ``is_callee`` identifies a called binding, imported target, or callable output
    without requiring the profiler to match source names.
    Read qualifiers describe possible relationships: ``is_variable_read`` marks
    possible binding reads; ``is_callable_read`` marks reading a callable through
    its output's scope without adding an edge to that scope.
    ``read_contribution_count`` and ``callable_read_count`` contribute to source-read
    totals, independent of dependency multiplicity. Each occurrence contributes
    once through a representative edge. Alternative bindings and callable
    outputs retain their read roles even when their counting contribution is
    zero; repeated source occurrences still contribute individually.
    Binding edges link a binding to variable versions or callable scopes.
    Declaration edges identify a node's declared scope or an imported class's
    source scope. Neither carries read or write dependency qualifiers. Different types between the same endpoints
    have independent counts.
    """

    dependency: 'Node | Scope'
    count: int  # type: ignore[assignment]  # Public field intentionally shadows tuple.count.
    access: AccessMode | None
    edge_type: EdgeType
    is_call_argument: bool = False
    is_callee: bool = False
    is_variable_read: bool = False
    is_callable_read: bool = False
    read_contribution_count: int = 0
    callable_read_count: int = 0


@dataclass(frozen=True, eq=False)
class Node:
    """A data item or expression node in a scope dependency graph."""

    name: str
    scope: 'Scope'
    display_name: str = field(kw_only=True)
    kind: NodeKind = NodeKind.RESULT
    operation_type: OperationType | None = None
    access: AccessMode | None = None
    dependency_edges: tuple[DependencyEdge, ...] = ()
    is_instance_attribute: bool = False
    is_class_attribute: bool = False
    is_global_write: bool = False
    is_nonlocal_write: bool = False
    is_named_endpoint: bool = False
    is_version_merge: bool = False
    is_generator_expression: bool = False
    is_import: bool = False
    is_unresolved: bool = False
    output_type: OutputType | None = None

    @property
    def is_builtin(self) -> bool:
        return self.scope.kind == ScopeKind.BUILTINS

    @property
    def deps(self) -> tuple['Node | Scope', ...]:
        return tuple({
            id(edge.dependency): edge.dependency for edge in self.dependency_edges
            if edge.edge_type.is_dependency
        }.values())

    def collect_call_targets(self) -> tuple[tuple[Node | Scope, ...], tuple[Node | Scope, ...]]:
        """Return known callable identities and external targets from resolved graph edges."""
        module_scope = _find_module_scope(self.scope)
        resolved: dict[int, Node | Scope] = {}
        external: dict[int, Node | Scope] = {}
        measured_dependencies = set()
        for edge in self.dependency_edges:
            if not edge.edge_type.is_dependency or not edge.is_callee:
                continue
            dep = edge.dependency
            if id(dep) in measured_dependencies:
                continue
            measured_dependencies.add(id(dep))
            if not isinstance(dep, Node):
                if self.kind == NodeKind.CALL and edge.is_callee:
                    resolved[id(dep)] = dep
                    if _find_module_scope(dep) is not module_scope:
                        external[id(dep)] = dep
                continue
            if edge.is_callee:
                for declared_target in _collect_declared_call_targets(dep):
                    resolved[id(declared_target)] = declared_target
                    if _find_module_scope(declared_target) is not module_scope:
                        external[id(declared_target)] = declared_target
                builtin_targets = _collect_target_nodes(dep, ScopeKind.BUILTINS)
                targets = _collect_target_nodes(dep, ScopeKind.ROOT)
                if targets:
                    outputs = _collect_callable_outputs(targets)
                    for output in outputs:
                        callable_target = output.scope if isinstance(output, Node) else output
                        if _find_module_scope(callable_target) is not module_scope:
                            external[id(output)] = output
                        if callable_target.kind != ScopeKind.ROOT:
                            resolved[id(callable_target)] = callable_target
                    if not outputs and not builtin_targets:
                        for target in targets:
                            external[id(target)] = target
                for target in builtin_targets:
                    resolved[id(target)] = target
                    external[id(target)] = target
            if (
                _is_callable_output(dep)
                and self.kind == NodeKind.CALL
                and edge.is_callee
            ):
                resolved[id(dep.scope)] = dep.scope
                if _find_module_scope(dep.scope) is not module_scope:
                    external[id(dep)] = dep
        output_scopes = {
            id(target.scope) for target in external.values() if isinstance(target, Node)
            and _is_callable_output(target)
        }
        return tuple(resolved.values()), tuple(
            target for target in external.values()
            if isinstance(target, Node) or id(target) not in output_scopes
        )


def _collect_declared_call_targets(dependency: Node | Scope) -> list[Scope]:
    targets = {}
    pending = [dependency]
    visited = set()
    while pending:
        candidate = pending.pop()
        if id(candidate) in visited:
            continue
        visited.add(id(candidate))
        if not isinstance(candidate, Node):
            if candidate.kind in (ScopeKind.CLASS, ScopeKind.FUNCTION):
                targets[id(candidate)] = candidate
            continue
        if candidate.output_type is not None:
            continue
        declarations = [
            edge.dependency for edge in candidate.dependency_edges
            if edge.edge_type is EdgeType.DECLARATION
        ]
        if declarations:
            pending.extend(declarations)
        elif candidate.is_import or candidate.scope.kind is ScopeKind.ROOT:
            pending.extend(candidate.deps)
        elif candidate.kind.is_value or candidate.kind is NodeKind.BINDING:
            pending.extend(
                edge.dependency for edge in candidate.dependency_edges
                if edge.edge_type is EdgeType.DATA and edge.is_variable_read
            )
    return list(targets.values())


def _collect_target_nodes(
    dependency: Node | Scope, target_scope: ScopeKind
) -> list[Node]:
    targets = {}
    pending = [dependency]
    visited = set()
    while pending:
        candidate = pending.pop()
        if (
            not isinstance(candidate, Node) or id(candidate) in visited
            or candidate.output_type is not None
        ):
            continue
        visited.add(id(candidate))
        if candidate.scope.kind is target_scope:
            targets[id(candidate)] = candidate
        elif candidate.is_import or candidate.scope.kind is ScopeKind.ROOT:
            pending.extend(candidate.deps)
        elif any(
            edge.edge_type is EdgeType.DECLARATION
            for edge in candidate.dependency_edges
        ):
            # Declaration inputs describe defaults and decorators, not identity.
            continue
        elif not candidate.kind.is_value and candidate.kind is not NodeKind.BINDING:
            # Operands of computed callees do not establish callable identity.
            # Resolution supplies known targets as separate callee dependencies.
            continue
        else:
            pending.extend(
                edge.dependency
                for edge in candidate.dependency_edges
                if edge.edge_type is EdgeType.DATA
                and (
                    edge.is_variable_read
                    or (
                        isinstance(edge.dependency, Node)
                        and edge.dependency.kind is NodeKind.REFERENCE
                    )
                )
            )
    return list(targets.values())


def _collect_callable_outputs(targets: list[Node]) -> list[Node | Scope]:
    outputs: dict[int, Node | Scope] = {}
    pending: list[Node | Scope] = list(targets)
    visited = set()
    while pending:
        candidate = pending.pop()
        if id(candidate) in visited:
            continue
        visited.add(id(candidate))
        if not isinstance(candidate, Node):
            if candidate.kind in (ScopeKind.FUNCTION, ScopeKind.CLASS):
                outputs[id(candidate)] = candidate
            continue
        if _is_callable_output(candidate):
            outputs[id(candidate)] = candidate
            continue
        if candidate.scope.kind is ScopeKind.ROOT and not candidate.deps:
            outputs[id(candidate)] = candidate
            continue
        if candidate.is_import or candidate.scope.kind is ScopeKind.ROOT:
            pending.extend(
                edge.dependency for edge in candidate.dependency_edges
                if edge.edge_type.is_dependency or edge.edge_type is EdgeType.DECLARATION
            )
        elif candidate.kind.is_value or candidate.kind is NodeKind.BINDING:
            declarations = [
                edge.dependency for edge in candidate.dependency_edges
                if edge.edge_type is EdgeType.DECLARATION
            ]
            pending.extend(declarations or [
                edge.dependency for edge in candidate.dependency_edges
                if edge.edge_type is EdgeType.DATA and edge.is_variable_read
            ])
    output_scopes = {
        id(output.scope) for output in outputs.values() if isinstance(output, Node)
    }
    return [
        output for output in outputs.values()
        if isinstance(output, Node) or id(output) not in output_scopes
    ]


def _is_callable_output(node: Node) -> bool:
    return (
        node.scope.kind is ScopeKind.FUNCTION
        and node.output_type in (OutputType.RETURN, OutputType.YIELD)
    )


def _find_module_scope(scope: Scope) -> Scope:
    while (
        scope.kind != ScopeKind.MODULE
        and scope.parent is not None
        and scope.parent.kind != ScopeKind.ROOT
    ):
        scope = scope.parent
    return scope
