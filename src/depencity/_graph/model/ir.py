from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass, field

from depencity._graph.model.enums import (
    AccessMode,
    NodeKind,
    OperationType,
    OutputType,
    ScopeKind,
)
from depencity._graph.model.reference import Reference


@dataclass(frozen=True, eq=False)
class DependencyInput:
    """One occurrence; structural inputs connect the graph without a source read.

    Equal references still have distinct occurrence identities.
    """

    name: str | Reference
    access: AccessMode | None
    is_structural: bool = False
    is_predicate: bool = False
    is_callee: bool = False
    is_call_argument: bool = False
    source: Reference | None = field(default=None, repr=False)


def collect_inputs(
    names: list[str | Reference], access: AccessMode | None,
    *, is_structural: bool = False, is_callee: bool = False,
    is_call_argument: bool = False,
) -> list[DependencyInput]:
    return [
        DependencyInput(name.description, access, is_structural=is_structural, source=name,
                        is_callee=is_callee, is_call_argument=is_call_argument)
        if isinstance(name, Reference) and name.read_scope is not None
        else DependencyInput(name, access, is_structural=is_structural,
                             is_callee=is_callee, is_call_argument=is_call_argument)
        for name in names
    ]


@dataclass(frozen=True)
class AnnotationHint:
    """A type expression with the lexical context that gives it meaning.

    Local declarations capture a cursor; parameter hints keep the enclosing
    scope's final lookup with ``position=None``. Copies preserve that policy.
    Hints are resolution metadata, never graph entities.
    """

    name: str
    scope: ScopeRecord
    position: int | None
    type_parameters: frozenset[str] = field(default_factory=frozenset)
    environment: BindingEnvironment | None = field(default=None, compare=False, repr=False)

    def parse_class_name(self, expression: ast.expr | None = None) -> list[str]:
        """Normalize a supported class name without interpreting type parameters."""
        if expression is None:
            expression = ast.parse(self.name, mode='eval').body
        if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
            try:
                expression = ast.parse(expression.value, mode='eval').body
            except SyntaxError:
                return []
        if not isinstance(expression, (ast.Name, ast.Attribute)):
            return []
        parts = ast.unparse(expression).split('.')
        return [] if parts[0] in self.type_parameters else parts


type AnnotationEvent = tuple[
    tuple[int, int, int, int] | None, set[AnnotationHint],
    tuple[int, int] | None, frozenset[tuple[NodeRecord, bool]],
]


@dataclass(eq=False)
class NodeRecord:
    """Mutable analysis and resolution data; name is only a description."""

    name: str
    scope: 'ScopeRecord'
    reference: Reference | None = None
    kind: NodeKind = NodeKind.RESULT
    operation_type: OperationType | None = None
    access: AccessMode | None = None
    binding: str | None = None
    binding_node: NodeRecord | None = field(default=None, repr=False)
    bound_scopes: list[ScopeRecord] = field(default_factory=list, repr=False)
    is_first_positional_parameter: bool = field(default=False, repr=False)
    target: str | None = None
    inputs: list[DependencyInput] = field(default_factory=list)
    value_sources: list[str | Reference] = field(default_factory=list, repr=False)
    raw_receiver_deps: list[str | Reference] = field(default_factory=list, repr=False)
    raw_calls: list[str] = field(default_factory=list)
    # Endpoint order and occurrence metadata share one authoritative map.
    # An empty occurrence map represents an unqualified dependency.
    deps: dict[
        'NodeRecord | ScopeRecord', dict[DependencyInput | None, AccessMode | None]
    ] = field(default_factory=dict, repr=False)
    read_targets: dict[
        DependencyInput, tuple['NodeRecord | ScopeRecord', ...]
    ] = field(default_factory=dict, repr=False)
    span: tuple[int, int, int, int] | None = None
    display_name: str | None = None
    is_instance_attribute: bool = False
    is_class_attribute: bool = False
    is_global_write: bool = False
    is_nonlocal_write: bool = False
    attribute_expression: ast.Attribute | None = field(default=None, repr=False)
    is_generator_expression: bool = False
    # Source computations feed handler conditions; bindings and declarations do not.
    is_computation: bool = False
    subscript_expression: ast.Subscript | None = field(default=None, repr=False)
    is_import: bool = False
    is_unresolved: bool = False
    is_deletion: bool = False
    # Earlier values can reappear at this cursor after partial body execution.
    binding_uncertainty_start: int | None = None
    output_type: OutputType | None = None
    inferred_types: set[AnnotationHint] = field(default_factory=set, repr=False)
    # Updates carry the source position where prior hints become possible again.
    inferred_type_events: list[AnnotationEvent] = field(default_factory=list, repr=False)
    inferred_classes: set[ScopeRecord] = field(default_factory=set, repr=False)
    class_object_targets: set[ScopeRecord] = field(default_factory=set, repr=False)
    callable_targets: set[ScopeRecord] = field(default_factory=set, repr=False)
    resolved_call_targets: set[ScopeRecord] = field(default_factory=set, repr=False)
    resolved_class_targets: set[ScopeRecord] = field(default_factory=set, repr=False)
    # Canonical callees awaiting final dependency-edge selection.
    resolved_import_targets: set[NodeRecord] = field(default_factory=set, repr=False)
    predicates: list['NodeRecord'] = field(default_factory=list, repr=False)
    # Operation gating does not necessarily make a completed binding optional.
    binding_conditions: list['NodeRecord'] = field(default_factory=list, repr=False)
    # Predicate edges share one test; binding invalidation must distinguish arms.
    branch_context: frozenset[tuple[NodeRecord, bool]] = field(
        default_factory=frozenset, repr=False,
    )
    is_dynamic_call: bool = False
    is_super_call: bool = False
    super_member: str | None = None
    decorator_reads: list[Reference] = field(default_factory=list, repr=False)
    declared_scope: 'ScopeRecord | None' = field(
        default=None, repr=False, compare=False
    )
    scope_position: int | None = field(default=None, repr=False)
    binding_visibility_end: int | None = field(default=None, repr=False)

    @property
    def raw_callee_deps(self) -> list[str | Reference]:
        return [
            occurrence.source or occurrence.name
            for occurrence in self.inputs if occurrence.is_callee
        ]

    @property
    def raw_deps(self) -> list[str | Reference]:
        return [occurrence.name for occurrence in self.inputs]

    def preserves_binding_at(self, position: int | None = None) -> bool:
        # Protected deletions retain prior candidates throughout the construct.
        return self.binding_uncertainty_start is not None and (
            self.is_deletion or position is None or position >= self.binding_uncertainty_start
        )

    def find_bindings(self, name: str | Reference) -> list[NodeRecord]:
        """Use the source read's lookup point, rather than its consumer's position."""
        if isinstance(name, str):
            for reference in self.raw_callee_deps:
                if isinstance(reference, Reference) and reference.read_scope is not None:
                    if reference.description == name:
                        return self.scope.find_nodes(reference, before=self)
                    continue
                for callee in self.scope.find_nodes(reference, before=self):
                    if callee.attribute_expression is not None:
                        return callee.find_bindings(name)
        sources = [
            occurrence.source or occurrence.name
            for occurrence in self.inputs
            if occurrence.name == name
        ]
        if sources:
            return list(dict.fromkeys(
                binding for source in sources
                for binding in self.scope.find_nodes(source, before=self)
            ))
        if self.attribute_expression is not None or self.subscript_expression is not None:
            for occurrence in self.inputs:
                for receiver in self.scope.find_nodes(
                    occurrence.source or occurrence.name, before=self
                ):
                    if (
                        receiver.attribute_expression is not None
                        or receiver.subscript_expression is not None
                    ):
                        return receiver.find_bindings(name)
        return self.scope.find_nodes(name, before=self)

    def collect_value_inputs(self) -> list[DependencyInput]:
        return [occurrence for occurrence in self.inputs if not occurrence.is_predicate]

    def collect_forwarded_dependencies(
        self, stop: NodeRecord | None = None,
    ) -> set[NodeRecord | ScopeRecord]:
        """Follow import and linear-alias paths without entering computations."""
        dependencies: set[NodeRecord | ScopeRecord] = set()
        pending = [self]
        visited = set()
        while pending:
            alias = pending.pop()
            if alias is stop or alias in visited:
                continue
            visited.add(alias)
            dependencies.update(alias.class_object_targets)
            for dependency in alias.deps:
                if dependency is stop:
                    continue
                dependencies.add(dependency)
                if isinstance(dependency, NodeRecord) and (
                    dependency.is_import or dependency.scope.kind == ScopeKind.ROOT
                    or dependency.binding is not None
                    and len(dependency.collect_value_inputs()) == 1
                ):
                    pending.append(dependency)
        return dependencies

    def collect_type_hints(self, before: NodeRecord | None = None) -> set[AnnotationHint]:
        if before is not None and self.inferred_type_events:
            scope: ScopeRecord | None = before.scope
            while scope is not None and scope is not self.scope:
                if scope.kind == ScopeKind.FUNCTION or (
                    scope.kind == ScopeKind.COMPREHENSION and scope.is_lazy_comprehension
                ):
                    before = None
                    break
                scope = scope.parent
            if scope is None:
                # Unrelated scopes do not share a source-position cursor.
                before = None
        events: Sequence[AnnotationEvent] = self.inferred_type_events
        pending = [before] if before is not None else []
        visited = set()
        while pending:
            consumer = pending.pop()
            if consumer in visited:
                continue
            visited.add(consumer)
            for occurrence in consumer.collect_read_inputs():
                source = occurrence.source
                if source is None and isinstance(occurrence.name, Reference):
                    source = occurrence.name
                environment = source.environment if source is not None else None
                while environment is not None and self not in environment.type_events:
                    environment = environment.parent
                if environment is not None:
                    events = environment.type_events[self][1]
                    pending.clear()
                    break
                if source is not None and source.read_scope is None:
                    pending.extend(consumer.scope.find_nodes(source, before=consumer))
        hints = set()
        for span, update, merge_from, branches in reversed(events):
            if before is not None and any(
                (condition, not arm) in before.branch_context for condition, arm in branches
            ):
                continue
            if (
                before is None
                or before.span is not None and span is not None and span[:2] <= before.span[:2]
            ):
                hints.update(update)
                if merge_from is None or (
                    before is not None and before.span is not None and before.span[:2] < merge_from
                ):
                    return hints
        return hints | self.inferred_types

    def collect_read_targets(
        self,
    ) -> dict[DependencyInput, tuple[NodeRecord | ScopeRecord, ...]]:
        """Resolve source occurrences to endpoints without mutating the IR."""
        read_targets: dict[DependencyInput, tuple[NodeRecord | ScopeRecord, ...]] = {}
        reads = self.collect_read_inputs()
        if not reads:
            return read_targets
        source_dependencies = []
        for dependency in self.deps:
            if not isinstance(dependency, NodeRecord) or dependency.is_unresolved:
                continue
            inputs = self.deps[dependency]
            if inputs and all(
                occurrence is not None and occurrence.is_structural
                for occurrence in inputs
            ):
                continue
            source_dependencies.append(dependency)
        has_unresolved_call = any(
            isinstance(dependency, NodeRecord)
            and dependency.is_unresolved
            and dependency.binding in self.raw_calls
            for dependency in self.deps
        )
        for occurrence in reads:
            name = occurrence.name
            source_targets = tuple(
                dependency for dependency in source_dependencies
                if dependency.reference is name or (
                    dependency.kind is NodeKind.VARIABLE
                    and dependency.binding == name
                )
            )
            contributed_targets = tuple(
                dependency for dependency in source_targets
                if occurrence in self.deps[dependency]
            )
            source_targets = (
                contributed_targets if occurrence.source is not None
                else contributed_targets or source_targets
            )
            builtin_targets = tuple(
                target for target in source_targets if target.scope.kind == ScopeKind.BUILTINS
            )
            targets: tuple[NodeRecord | ScopeRecord, ...] = tuple(
                target for target in source_targets if target.scope.kind != ScopeKind.BUILTINS
            )
            if not targets and self.reference is name and self.binding is None:
                targets = (self,)
            if not targets:
                targets = tuple(
                    dependency for dependency in self.deps
                    if isinstance(dependency, ScopeRecord) and dependency.symbol == name
                    and (
                        occurrence.source is None
                        or occurrence in self.deps[dependency]
                        or occurrence.is_callee and name in self.raw_calls
                    )
                )
            if not targets and name == '__class__':
                class_scope = self.scope.find_class_cell_scope(occurrence.source or name)
                targets = tuple(
                    dependency for dependency in self.deps
                    if (
                        isinstance(dependency, ScopeRecord)
                        and class_scope is not None and dependency is class_scope
                    ) or (
                        isinstance(dependency, NodeRecord)
                        and class_scope is not None
                        and dependency.declared_scope is class_scope
                    )
                )
            if (
                not targets
                and self.kind == NodeKind.CALL
                and occurrence.is_callee
                and (name in self.raw_calls or isinstance(name, Reference))
                and not has_unresolved_call
            ):
                call_name = self.raw_calls[0] if isinstance(name, Reference) else name
                targets = tuple(dict.fromkeys(
                    dependency.scope for dependency in self.deps
                    if isinstance(dependency, NodeRecord)
                    and dependency.output_type is not None
                    and dependency.scope.symbol == call_name
                ))
            targets = (*targets, *builtin_targets)
            if not targets:
                targets = tuple(
                    dependency for dependency in self.deps
                    if isinstance(dependency, NodeRecord)
                    and dependency.is_unresolved
                    and occurrence in self.deps[dependency]
                )
            read_targets[occurrence] = targets
        return read_targets

    def collect_read_inputs(self) -> list[DependencyInput]:
        """Select source reads without structural, predicate, or write-target bookkeeping.

        A resolved write target contributes once. The first unresolved target
        of an ordinary assignment is bookkeeping rather than a read.
        Bare-name deletion invalidates a binding without reading its value.
        """
        if self.is_deletion:
            return []
        inputs = [
            occurrence for occurrence in self.inputs
            if not occurrence.is_structural and not occurrence.is_predicate
        ]
        if self.access != AccessMode.WRITE or self.target is None:
            return inputs
        target_is_resolved = any(
            isinstance(dependency, NodeRecord)
            and not dependency.is_unresolved
            and (
                dependency.reference is self.target
                or (
                    dependency.kind is NodeKind.VARIABLE
                    and dependency.binding == self.target
                )
            )
            for dependency in self.deps
        )
        reads = []
        seen_target = False
        for occurrence in inputs:
            if occurrence.source is None and occurrence.name == self.target:
                if target_is_resolved:
                    if seen_target:
                        continue
                elif self.operation_type != OperationType.MUTATION and not seen_target:
                    seen_target = True
                    continue
                seen_target = True
            reads.append(occurrence)
        return reads

    def add_dependency(
        self,
        dependency: 'NodeRecord | ScopeRecord',
        occurrence: DependencyInput | None = None,
        *,
        access: AccessMode | None = None,
    ) -> None:
        # Re-resolving an occurrence must not count it twice. A direct member
        # access uses the None key because that relation occurs once per node.
        inputs = self.deps.setdefault(dependency, {})
        if occurrence is not None or access is not None:
            inputs[occurrence] = (
                occurrence.access if occurrence is not None else access
            )

    def replace_dependency(
        self,
        dependency: 'NodeRecord | ScopeRecord',
        replacement: 'NodeRecord | ScopeRecord',
    ) -> None:
        dependencies: dict[NodeRecord | ScopeRecord, dict[DependencyInput | None, AccessMode | None]] = {}
        for target, inputs in self.deps.items():
            if target is dependency:
                target = replacement
            dependencies.setdefault(target, {}).update(inputs)
        # Preserve the replaced occurrence's access when endpoints converge.
        dependencies[replacement].update(self.deps[dependency])
        self.deps = dependencies


@dataclass(frozen=True)
class BindingEnvironment:
    """Local candidates at a construction boundary; never a graph entity."""

    scope: ScopeRecord
    position: int
    bindings: dict[str | Reference, list[NodeRecord]]
    definite_names: frozenset[str | Reference]
    parent: BindingEnvironment | None = None
    active_conditions: frozenset[NodeRecord] = frozenset()
    # Each binding stores its consumed event count and captured annotation history.
    type_events: dict[NodeRecord, tuple[int, tuple[AnnotationEvent, ...]]] = field(default_factory=dict)

    def advance(self, position: int) -> BindingEnvironment:
        """Resume this state after skipping a sibling suite's records."""
        return BindingEnvironment(
            self.scope, position, self.bindings, self.definite_names, self.parent,
            self.active_conditions,
            {
                binding: (len(binding.inferred_type_events), events)
                for binding, (_, events) in self.type_events.items()
            },
        )

    def merge(self, other: BindingEnvironment, position: int) -> BindingEnvironment:
        """Keep this entry state and the additional possible branch values."""
        bindings = {name: list(nodes) for name, nodes in self.bindings.items()}
        for name, nodes in other.bindings.items():
            bindings[name] = list(dict.fromkeys([*bindings.get(name, []), *nodes]))
        return BindingEnvironment(
            self.scope, position, bindings, self.definite_names, self.parent,
            self.active_conditions,
            {**other.type_events, **self.type_events},
        ).advance(position)


@dataclass(eq=False)
class ScopeRecord:
    """Lexical analysis state and ordered records, completed before graph creation."""

    name: str
    kind: ScopeKind
    parent: ScopeRecord | None = None
    symbol: str | Reference | None = None
    children: list[ScopeRecord] = field(default_factory=list)
    nodes: list[NodeRecord] = field(default_factory=list)
    outputs: list[NodeRecord] = field(default_factory=list)
    bindings: dict[str, list[NodeRecord]] = field(default_factory=dict)
    span: tuple[int, int, int, int] | None = None
    class_declaration: NodeRecord | None = None
    defines: set[str] = field(default_factory=set)
    global_decls: set[str] = field(default_factory=set)
    nonlocal_decls: set[str] = field(default_factory=set)
    type_parameter_bindings: dict[str, NodeRecord] = field(default_factory=dict)
    # Base value references; unknown bases retain their positions for super checks.
    base_reads: list[Reference | None] = field(default_factory=list)
    is_standalone_module: bool = False
    is_package_initializer: bool = False
    return_types: set[AnnotationHint] = field(default_factory=set, repr=False)
    is_lazy_comprehension: bool = False

    def find_nodes(
        self, name: str | Reference, before: NodeRecord | None = None,
        position: int | None = None,
        environment: BindingEnvironment | None = None,
        active_conditions: frozenset[NodeRecord] = frozenset(),
    ) -> list[NodeRecord]:
        """Return definitions in the visible lexical binding.

        A name can have several data versions after reassignment or branching.
        Keep the latest unconditional definition and any later conditional
        alternatives. ``position`` records a source read's cursor; ``before``
        supplies a consumer's cursor for non-read relationships. Both restrict
        versions in this scope. Eager comprehension reads capture their enclosing
        lookup point; deferred parent-scope lookups use final visible versions.
        Control-flow precision is intentionally outside this model.

        Expression identities can directly reference a child scope's output;
        this does not expose the child's lexical bindings to its parent.
        """
        if isinstance(name, Reference) and name.read_scope is not None:
            return name.read_scope.find_nodes(
                name.description, position=name.read_position,
                environment=name.environment,
            )
        position = (
            before.scope_position
            if before is not None and before.scope is self
            else position
        )
        if isinstance(name, Reference):
            for child in self.children:
                for output in child.outputs:
                    if output.reference is name:
                        return [output]
        if isinstance(name, Reference):
            candidates = [node for node in self.nodes if node.reference is name]
        else:
            candidates = [
                node for node in self.bindings.get(name, [])
                if node is not self.type_parameter_bindings.get(name)
            ]
        local_before = before if before is not None and before.scope is self else None
        local_environment = self.capture_binding_environment(
            {name: candidates}, local_before, position=position,
            active_conditions=active_conditions, environment=environment,
        )
        visible = local_environment.bindings.get(name, [])
        definite = name in local_environment.definite_names
        eager = position is not None or before is not None
        if name in self.global_decls and self.kind != ScopeKind.MODULE:
            module = self.find_module_scope()
            if not visible:
                return self._find_enclosing_nodes(
                    name, owner=module, eager=eager, environment=environment,
                )
            if definite:
                return visible
            return [*self._find_enclosing_nodes(
                name, owner=module, eager=eager, environment=environment,
            ), *visible]

        if name in self.nonlocal_decls:
            parent = self._find_lexical_parent()
            class_scope = self.find_class_cell_scope(name)
            if class_scope is not None and class_scope.class_declaration is not None:
                inherited = [class_scope.class_declaration]
            else:
                inherited = (
                    self._find_enclosing_nodes(
                        name, owner=parent, eager=eager, environment=environment,
                    )
                    if parent is not None else []
                )
            if not visible or definite:
                return visible or inherited
            return [*inherited, *visible]

        if candidates or visible:
            if self.kind == ScopeKind.CLASS and visible:
                if any(node.is_deletion for node in visible) or not definite:
                    return [*self._find_enclosing_nodes(
                        name, eager=eager, environment=environment,
                    ), *visible]
            if position is not None or before is not None and before.scope is self:
                if visible or (
                    self.kind != ScopeKind.CLASS
                    and name not in self.global_decls | self.nonlocal_decls
                ):
                    return visible
            else:
                return visible

        if self.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION) and name in self.defines:
            return []

        type_parameter = self.type_parameter_bindings.get(name) if isinstance(name, str) else None
        if type_parameter is not None and not (
            self.kind == ScopeKind.CLASS and name in self.defines
        ):
            return [type_parameter]

        class_scope = self.find_class_cell_scope(name)
        if class_scope is not None:
            declaration = class_scope.class_declaration
            if declaration is not None and declaration.declared_scope is class_scope:
                return [declaration]
            return []

        return self._find_enclosing_nodes(
            name, eager=eager, environment=environment,
        )

    def find_binding_scope(self, name: str) -> ScopeRecord:
        scope = self
        if name in scope.global_decls:
            return self.find_module_scope()
        elif name in scope.nonlocal_decls:
            lookup_scope = (
                scope.parent if scope.kind == ScopeKind.CLASS and scope.parent is not None else scope
            )
            class_scope = lookup_scope.find_class_cell_scope(name)
            if class_scope is not None:
                return class_scope
            parent = scope.parent
            while parent is not None:
                if (
                    parent.kind == ScopeKind.FUNCTION
                    and (name in parent.defines or name in parent.bindings)
                    and name not in parent.global_decls | parent.nonlocal_decls
                ):
                    return parent
                parent = parent.parent
        return scope

    def find_module_scope(self) -> ScopeRecord:
        scope = self
        while scope.parent is not None and scope.kind != ScopeKind.MODULE:
            scope = scope.parent
        return scope

    def find_member_nodes(self, name: str) -> list[NodeRecord]:
        """Select bindings owned by this class namespace."""
        if name in self.global_decls | self.nonlocal_decls:
            return []
        return self.capture_binding_environment({
            name: [binding for binding in self.bindings.get(name, [])
                   if binding is not self.type_parameter_bindings.get(name)],
        }).bindings.get(name, [])

    def find_class_cell_scope(self, name: str | Reference) -> ScopeRecord | None:
        if isinstance(name, Reference):
            if name.read_scope is not None:
                return name.read_scope.find_class_cell_scope(name.description)
            name = name.description
        if name != '__class__':
            return None
        current = self
        while current.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION):
            if name in current.type_parameter_bindings or name in current.global_decls or (
                name in current.defines and name not in current.nonlocal_decls
            ):
                return None
            if current.parent is None:
                return None
            current = current.parent
        return current if current.kind == ScopeKind.CLASS and current is not self else None

    def _find_enclosing_nodes(
        self, name: str | Reference, owner: ScopeRecord | None = None,
        *, eager: bool, environment: BindingEnvironment | None = None,
    ) -> list[NodeRecord]:
        # A class-local declaration prevents capturing a same-named function
        # variable, even before the class binding has a visible value.
        if self.kind == ScopeKind.CLASS and owner is None and name in self.defines:
            owner = self.find_module_scope()
        eager_scope = self
        while (
            eager_scope.kind == ScopeKind.COMPREHENSION
            and not eager_scope.is_lazy_comprehension
            and eager_scope.parent is not None
        ):
            eager_scope = eager_scope.parent
        if eager and eager_scope.kind == ScopeKind.CLASS and eager_scope.class_declaration is not None:
            parent = eager_scope.parent
            before: NodeRecord | None = eager_scope.class_declaration
            while parent is not None and parent.kind == ScopeKind.CLASS:
                before = parent.class_declaration
                parent = parent.parent
            if parent is not None and (owner is None or parent is owner):
                return parent.find_nodes(
                    name, before=before, environment=environment,
                )
        if owner is not None:
            return owner.find_nodes(name)
        parent = self.parent
        while parent is not None:
            if parent.kind == ScopeKind.ROOT:
                return []
            if parent.kind == ScopeKind.CLASS:
                type_parameter = (
                    parent.type_parameter_bindings.get(name) if isinstance(name, str) else None
                )
                if type_parameter is not None:
                    return [type_parameter]
            else:
                bindings = parent.find_nodes(name)
                if bindings:
                    return bindings
                if (
                    parent.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION)
                    and name in parent.defines
                ):
                    return []
            parent = parent.parent
        return []

    def _find_lexical_parent(self) -> ScopeRecord | None:
        parent = self.parent
        if self.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION) and parent is not None:
            if parent.kind == ScopeKind.CLASS:
                parent = parent.parent
        while parent is not None and parent.kind == ScopeKind.CLASS:
            parent = parent.parent
        return parent

    def find_current_nodes(
        self, name: str, environment: BindingEnvironment | None = None,
    ) -> list[NodeRecord]:
        """Return the currently visible versions bound in this scope."""
        local_environment = self.capture_binding_environment({
            name: self.bindings.get(name, []),
        }, environment=environment)
        visible = local_environment.bindings.get(name, [])
        if name not in self.global_decls | self.nonlocal_decls:
            return visible
        if name in local_environment.definite_names:
            return visible

        parent = self.parent
        if name in self.global_decls:
            while parent is not None and parent.kind != ScopeKind.MODULE:
                parent = parent.parent
        elif name in self.nonlocal_decls:
            parent = self._find_lexical_parent()
        inherited = parent.find_nodes(name) if parent is not None else []
        return [*inherited, *visible]

    def capture_binding_environment(
        self,
        bindings: dict[str | Reference, list[NodeRecord]] | None = None,
        before: NodeRecord | None = None,
        position: int | None = None,
        active_conditions: frozenset[NodeRecord] = frozenset(),
        environment: BindingEnvironment | None = None,
    ) -> BindingEnvironment:
        """Replay local writes into a name-to-candidates snapshot.

        Definite writes replace candidates; optional writes merge them. Lexical
        fallback stays with find_nodes rather than entering this local state.
        """
        position = (
            before.scope_position
            if before is not None and before.scope is self
            else position
        )
        context = environment
        while context is not None and context.scope is not self:
            context = context.parent
        if context is not None:
            active_conditions |= context.active_conditions
        start = context.position if context is not None else 0
        initial = context.bindings if context is not None else {}
        definite_names = set(context.definite_names) if context is not None else set()
        names = {
            node: name
            for name, nodes in (self.bindings if bindings is None else bindings).items()
            for node in nodes
            if (bindings is not None or not isinstance(name, str)
                or node is not self.type_parameter_bindings.get(name))
            and (node.scope is not self
            or node.binding_visibility_end is None
            or position is not None and position < node.binding_visibility_end)
        }
        ordered_nodes = list(self.nodes)
        ordered_ids = {id(node) for node in ordered_nodes}
        for node in names:
            if id(node) in ordered_ids or node.scope is self:
                continue
            insertion = next(
                (
                    index
                    for index, existing in enumerate(ordered_nodes)
                    if node.span is not None and existing.span is not None
                    and existing.span[:2] > node.span[:2]
                ),
                len(ordered_nodes),
            )
            ordered_nodes.insert(insertion, node)
            ordered_ids.add(id(node))
        selected = {
            name: list(nodes) for name, nodes in initial.items()
            if bindings is None or name in bindings
        }
        for node in ordered_nodes:
            if before is not None and node is before:
                break
            if (
                position is not None and node.scope is self
                and node.scope_position is not None and node.scope_position >= position
            ):
                break
            if node not in names or (
                context is not None and node.scope is self
                and node.scope_position is not None and node.scope_position < start
            ):
                continue
            name = names[node]
            if not self.is_binding_conditional(node, position, active_conditions):
                selected[name] = [node]
                definite_names.add(name)
                continue
            candidates = selected.setdefault(name, [])
            if node.is_deletion and not node.preserves_binding_at(position):
                # A guarded deletion replaces only bindings from its own region.
                predicates = set(node.predicates)
                candidates[:] = [
                    previous for previous in candidates
                    if not (
                        self.is_binding_conditional(previous, position, active_conditions)
                        and node.branch_context.issubset(previous.branch_context)
                        and predicates.issubset(previous.predicates)
                    )
                ]
            candidates.append(node)
        type_events = {}
        for nodes in selected.values():
            for binding in nodes:
                consumed, events = (
                    context.type_events.get(binding, (0, ()))
                    if context is not None else (0, ())
                )
                type_events[binding] = (
                    len(binding.inferred_type_events),
                    (*events, *binding.inferred_type_events[consumed:]),
                )
        return BindingEnvironment(
            self, len(self.nodes) if position is None else position,
            selected, frozenset(definite_names),
            context.parent if context is not None else environment,
            active_conditions,
            type_events,
        )

    def is_binding_conditional(
        self, node: NodeRecord, position: int | None = None,
        active_conditions: frozenset[NodeRecord] = frozenset(),
    ) -> bool:
        enclosing = (
            self.class_declaration.predicates
            if self.kind == ScopeKind.CLASS and self.class_declaration is not None
            else ()
        )
        return node.preserves_binding_at(position) or any(
            predicate not in enclosing and predicate not in active_conditions
            for predicate in node.binding_conditions
        )
