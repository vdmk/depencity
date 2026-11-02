from __future__ import annotations

import ast
from typing import cast

from depencity._graph.model.enums import (
    AccessMode,
    NodeKind,
    OperationType,
    OutputType,
    ScopeKind,
)
from depencity._graph.model.ir import (
    AnnotationHint,
    BindingEnvironment,
    DependencyInput,
    NodeRecord,
    ScopeRecord,
    collect_inputs,
)
from depencity._graph.model.reference import Reference

_REFERENCE_TYPES = (ast.Attribute, ast.Subscript)
_YIELD_TYPES = (ast.Yield, ast.YieldFrom)


def build_ir(
    tree: ast.Module,
    retained_import_names: set[str] | None = None,
    *, retain_unused_imports: bool = False,
) -> list[ScopeRecord]:
    """Build source IR, deferring import pruning when package uses are not known."""
    source_names = {
        value
        for node in ast.walk(tree)
        for attribute in ('id', 'arg', 'name', 'asname')
        if isinstance(value := getattr(node, attribute, None), str)
    }
    builder = ScopeBuilder(source_names)
    builder._visit_statements(tree.body)
    scopes = builder.all_scopes
    if not retain_unused_imports:
        retained_imports = {
            node for scope in scopes for node in scope.nodes
            if node.is_import and retained_import_names and node.binding in retained_import_names
            and node in node.scope.find_current_nodes(node.binding)
        }
        retained_imports.update(_collect_exported_imports(tree, scopes[1]))
        prune_unused_imports(scopes, retained_imports)
    return scopes


def _collect_exported_imports(tree: ast.Module, module: ScopeRecord) -> set[NodeRecord]:
    return {
        binding
        for name in _collect_literal_exports(tree) or ()
        for binding in module.find_current_nodes(name)
        if binding.is_import
    }


def _collect_literal_exports(tree: ast.Module) -> set[str] | None:
    declarations = [
        statement
        for statement in tree.body
        if isinstance(statement, (ast.Assign, ast.AnnAssign))
        and statement.value is not None
        and any(
            isinstance(target, ast.Name) and target.id == '__all__'
            for target in (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
        )
    ]
    if len(declarations) != 1:
        return None

    declaration = declarations[0]
    if isinstance(declaration, ast.Assign) and len(declaration.targets) != 1:
        return None
    value = declaration.value
    if not isinstance(value, (ast.List, ast.Tuple)):
        return None
    exports: set[str] = set()
    for item in value.elts:
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            return None
        exports.add(item.value)

    # Only a standalone literal declaration is exact. Any other reference or
    # binding can affect exports; use public-name discovery instead of evaluation.
    for statement in tree.body:
        if statement is declaration:
            continue
        for current in _walk_runtime_nodes(statement):
            if (
                isinstance(current, ast.Name) and current.id == '__all__'
                or getattr(current, 'name', None) == '__all__'
                or getattr(current, 'asname', None) == '__all__'
                or isinstance(current, ast.Import) and any(
                    alias.asname is None and alias.name.split('.')[0] == '__all__'
                    for alias in current.names
                )
                or isinstance(current, ast.MatchMapping) and current.rest == '__all__'
            ):
                return None
    return exports


def _walk_runtime_nodes(tree: ast.AST):
    """Walk represented references, excluding metadata and discarded bare names."""
    pending = [tree]
    while pending:
        current = pending.pop()
        if isinstance(current, ast.Expr) and isinstance(current.value, ast.Name):
            continue
        if isinstance(current, ast.AnnAssign) and current.value is None:
            target = current.target
            if isinstance(target, (ast.Attribute, ast.Subscript)):
                expressions: list[ast.AST] = [target.value]
                if isinstance(target, ast.Subscript):
                    expressions.extend(
                        ast.iter_child_nodes(target.slice)
                        if isinstance(target.slice, ast.Slice)
                        else [target.slice]
                    )
                pending.extend(
                    expression for expression in expressions
                    if not isinstance(expression, ast.Name)
                )
            continue
        yield current
        pending.extend(
            child for child in ast.iter_child_nodes(current)
            if child is not getattr(current, 'annotation', None)
            and child is not getattr(current, 'returns', None)
            and child not in getattr(current, 'type_params', ())
            and not (isinstance(current, ast.TypeAlias) and child is current.value)
        )


def prune_unused_imports(
    scopes: list[ScopeRecord], retained_imports: set[NodeRecord],
) -> None:
    used_imports = collect_used_imports(scopes) | retained_imports
    # Metadata must retain its original bindings until member resolution finishes.
    # This keeps imports available without introducing annotation data reads.
    annotation_hints = set()
    for scope in scopes:
        annotation_hints.update(scope.return_types)
        for node in scope.nodes:
            annotation_hints.update(node.inferred_types)
            for _, hints, _, _ in node.inferred_type_events:
                annotation_hints.update(hints)
    for hint in annotation_hints:
        for expression in ast.walk(ast.parse(hint.name, mode='eval')):
            if isinstance(expression, ast.Name):
                used_imports.update(
                    candidate
                    for candidate in hint.scope.find_nodes(
                        expression.id, position=hint.position, environment=hint.environment,
                    )
                )
    imports = [
        (node, node.binding) for scope in scopes for node in scope.nodes
        if node.is_import and node.binding is not None
    ]
    for node, binding in imports:
        if node in used_imports:
            continue
        scope = node.scope
        scope.nodes.remove(node)
        definitions = scope.bindings[binding]
        definitions.remove(node)
        if not definitions:
            del scope.bindings[binding]
    used_targets = {id(dep) for scope in scopes for node in scope.nodes for dep in node.deps}
    root = scopes[0]
    root.nodes[:] = [node for node in root.nodes if id(node) in used_targets]
    root.bindings = {cast(str, node.binding): [node] for node in root.nodes}


def collect_used_imports(scopes: list[ScopeRecord]) -> set[NodeRecord]:
    """Find imports through the lexical bindings consumed by source operations."""
    return {
        candidate
        for scope in scopes
        for current in scope.nodes
        for occurrence in current.inputs
        for candidate in scope.find_nodes(
            occurrence.source or occurrence.name, before=current,
        )
        if candidate.is_import
    }


class ScopeBuilder(ast.NodeVisitor):
    def __init__(self, source_names: set[str] | None = None):
        self.root = ScopeRecord('__root__', ScopeKind.ROOT)
        self.module = ScopeRecord(
            '__module__', ScopeKind.MODULE, parent=self.root,
            symbol='__module__', is_standalone_module=True
        )
        self.root.children.append(self.module)
        self.current = self.module
        self.all_scopes: list[ScopeRecord] = [self.root, self.module]
        self._counter = 0
        self._return_counters: dict[int, int] = {}
        self._condition_stack: list[NodeRecord] = []
        self._branch_context: frozenset[tuple[NodeRecord, bool]] = frozenset()
        self._binding_environment: BindingEnvironment | None = None
        self._interrupted_scopes: frozenset[ScopeRecord] = frozenset()
        self._nodes_by_id: dict[Reference, NodeRecord] = {}
        self._source_names = source_names or set()

    @staticmethod
    def _target_names(node: ast.expr):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Starred):
            yield from ScopeBuilder._target_names(node.value)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                yield from ScopeBuilder._target_names(elt)
        else:
            raise TypeError(f'unsupported assignment target: {type(node).__name__}')

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self._visit_scope(node, ScopeKind.FUNCTION)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef):
        self._visit_scope(node, ScopeKind.CLASS)

    def _visit_scope(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        kind: ScopeKind,
    ) -> None:
        saved_conditions = self._condition_stack
        record = ScopeRecord(
            name=node.name,
            symbol=node.name,
            kind=kind,
            span=self._span(node),
        )
        record.parent = self.current
        self._record_scope_bindings(node, record)
        if node.type_params:
            parent_scope = self.current
            self._condition_stack = []
            self.current = record
            self._add_type_parameter_bindings(node.type_params)
            self.current = parent_scope
            self._condition_stack = saved_conditions
        type_parameter_names = set(record.type_parameter_bindings)
        if isinstance(node, ast.ClassDef):
            type_parameter_expressions = [
                *node.bases,
                *(keyword.value for keyword in node.keywords),
            ]
        else:
            type_parameter_expressions = [
                default
                for default in (*node.args.defaults, *node.args.kw_defaults)
                if default is not None
            ]
        declaration_bindings = {
            expression: record.type_parameter_bindings
            for expression in type_parameter_expressions
            if any(
                child.id in type_parameter_names
                for child in ast.walk(expression)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
            )
        } or None
        dependencies = []
        decorator_reads = []
        for expression in self._declaration_expressions(node):
            if expression in node.decorator_list:
                decorator_reads.append(Reference(
                    ast.unparse(expression), self.current, len(self.current.nodes),
                    environment=self._capture_bindings(),
                ))
            expression_dependencies = self._record_expression_sequence(
                [expression], declaration_bindings,
            )
            if isinstance(node, ast.ClassDef) and expression in node.bases:
                base = expression.value if isinstance(expression, ast.Subscript) else expression
                while isinstance(base, ast.Attribute):
                    base = base.value
                if isinstance(base, ast.Name):
                    base_read = expression_dependencies[0]
                    assert isinstance(base_read, Reference)
                    if isinstance(expression, ast.Subscript):
                        occurrence = self._nodes_by_id[base_read].inputs[0]
                        base_read = occurrence.source or occurrence.name
                    assert isinstance(base_read, Reference)
                    record.base_reads.append(base_read)
                else:
                    record.base_reads.append(None)
            dependencies.extend(expression_dependencies)
        declaration_environment = self._capture_bindings()
        declaration = self._add_bound_node(
            node.name, dependencies, span=self._span(node)
        )
        declaration.decorator_reads = decorator_reads
        saved_branches = self._branch_context
        saved_environment = self._binding_environment
        self._binding_environment = declaration_environment if kind == ScopeKind.CLASS else None
        if kind == ScopeKind.FUNCTION:
            self._branch_context = frozenset()
        self._condition_stack = list(saved_conditions) if kind == ScopeKind.CLASS else []
        scope = self._push(record)
        declaration.declared_scope = scope
        if kind == ScopeKind.CLASS:
            scope.class_declaration = declaration
            declaration.class_object_targets.add(scope)
        if not scope.type_parameter_bindings:
            self._add_type_parameter_bindings(node.type_params)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._process_args(node.args)
        self._visit_statements(node.body)
        if kind == ScopeKind.FUNCTION and not self._suite_always_exits(node.body):
            self._add_none_return()
        if (
            isinstance(node, ast.FunctionDef)
            and isinstance(node.returns, (ast.Name, ast.Attribute, ast.Constant))
            and not any(output.output_type == OutputType.YIELD for output in scope.outputs)
        ):
            assert scope.parent is not None
            scope.return_types = self._collect_annotation_hints(
                node.returns, scope.parent, None, frozenset(scope.type_parameter_bindings),
            )
        self._pop()
        self._condition_stack = saved_conditions
        self._branch_context = saved_branches
        self._binding_environment = saved_environment

    def _record_scope_bindings(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda,
        scope: ScopeRecord,
    ) -> None:
        """Record complete lexical declarations without creating value versions."""
        pending: list[ast.AST] = [node.body] if isinstance(node, ast.Lambda) else list(node.body)
        while pending:
            current = pending.pop()
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                scope.defines.add(current.name)
                pending.extend(self._declaration_expressions(current))
                continue
            if isinstance(current, ast.Lambda):
                pending.extend(
                    default for default in (*current.args.defaults, *current.args.kw_defaults)
                    if default is not None
                )
                continue
            if isinstance(current, ast.TypeAlias):
                scope.defines.add(current.name.id)
                continue
            if isinstance(current, ast.comprehension):
                pending.extend((current.iter, *current.ifs))
                continue
            if isinstance(current, ast.AnnAssign):
                pending.append(current.target)
                if current.value is not None:
                    pending.append(current.value)
                continue
            if isinstance(current, ast.Global):
                scope.global_decls.update(current.names)
            elif isinstance(current, ast.Nonlocal):
                scope.nonlocal_decls.update(current.names)
            elif isinstance(current, (ast.Import, ast.ImportFrom)):
                scope.defines.update(
                    alias.asname or alias.name.split('.')[0]
                    for alias in current.names if alias.name != '*'
                )
            elif isinstance(current, ast.Name) and isinstance(current.ctx, (ast.Store, ast.Del)):
                scope.defines.add(current.id)
            elif isinstance(current, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and current.name:
                scope.defines.add(current.name)
            elif isinstance(current, ast.MatchMapping) and current.rest:
                scope.defines.add(current.rest)
            pending.extend(ast.iter_child_nodes(current))

    def visit_TypeAlias(self, node: ast.TypeAlias):
        # The alias value is lazy; binding the TypeAliasType itself does not
        # evaluate or depend on names in its value expression.
        self._add_bound_node(node.name.id, [], span=self._span(node))

    def _declaration_expressions(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> list[ast.expr]:
        expressions = list(node.decorator_list)
        if isinstance(node, ast.ClassDef):
            expressions.extend(node.bases)
            expressions.extend(keyword.value for keyword in node.keywords)
        else:
            expressions.extend(
                default
                for default in (*node.args.defaults, *node.args.kw_defaults)
                if default is not None
            )
        return expressions

    def _record_expression_sequence(
        self,
        expressions: list[ast.expr],
        declaration_bindings: dict[ast.expr, dict[str, NodeRecord]] | None = None,
    ) -> list[str | Reference]:
        dependencies: list[str | Reference] = []
        for expression in expressions:
            previous_context = self._binding_environment
            previous_bindings = {}
            if declaration_bindings and expression in declaration_bindings:
                for name, binding in declaration_bindings[expression].items():
                    previous_bindings[name] = self.current.bindings.get(name)
                    self.current.bindings[name] = [binding]
                self._binding_environment = self._capture_bindings()
            try:
                dependencies.extend(self._decompose_expr(expression))
            finally:
                self._binding_environment = previous_context
                for name, bindings in previous_bindings.items():
                    if bindings is None:
                        del self.current.bindings[name]
                    else:
                        self.current.bindings[name] = bindings
        return dependencies

    def visit_Assign(self, node: ast.Assign):
        rhs_dependencies = self._decompose_expr(node.value)
        for target in node.targets:
            self._assign_target(
                target,
                rhs_dependencies,
                span=self._span(node),
                extraction_display_name=(
                    ast.unparse(node) if isinstance(target, (ast.Tuple, ast.List)) else None
                ),
            )

    def visit_Delete(self, node: ast.Delete):
        for target in node.targets:
            self._add_delete_node(target)

    def _add_delete_node(self, target: ast.expr) -> None:
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._add_delete_node(element)
            return
        if isinstance(target, ast.Starred):
            self._add_delete_node(target.value)
            return
        if isinstance(target, ast.Name):
            self._add_name_deletion(target.id, self._span(target))
            return
        if isinstance(target, _REFERENCE_TYPES):
            self._add_reference_node(target, AccessMode.WRITE)
            return

    def _add_name_deletion(
        self,
        name: str,
        span: tuple[int, int, int, int],
    ) -> None:
        deleted_name = self._create_fresh_reference(f'delete_{name}')
        self.current.defines.add(name)
        deleted_node = self._append_node(
            NodeRecord(
                name=deleted_name.description,
                reference=deleted_name,
                scope=self.current,
                kind=NodeKind.OPERATION,
                operation_type=OperationType.MUTATION,
                is_computation=True,
                access=AccessMode.WRITE,
                is_global_write=name in self.current.global_decls,
                is_nonlocal_write=name in self.current.nonlocal_decls,
                target=name,
                inputs=collect_inputs(
                    self._decompose_expr(ast.Name(id=name, ctx=ast.Load())),
                    AccessMode.WRITE,
                ),
                span=span,
                is_deletion=True,
                binding_uncertainty_start=(
                    len(self.current.nodes) if self.current in self._interrupted_scopes else None
                ),
                display_name=f'del {name}',
            )
        )
        self.current.bindings.setdefault(name, []).append(deleted_node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        annotation_types = self._collect_annotation_hints(
            node.annotation, self.current, len(self.current.nodes),
            environment=self._capture_bindings(),
        )
        if node.value is None:
            if isinstance(node.target, ast.Name):
                if self.current.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION):
                    self.current.defines.add(node.target.id)
                for binding in self.current.find_current_nodes(
                    node.target.id, environment=self._binding_environment,
                ):
                    if binding.is_deletion:
                        continue
                    span = self._span(node)
                    binding.inferred_type_events.append(
                        (span, set(annotation_types), None, self._branch_context)
                    )
            elif isinstance(node.target, ast.Attribute):
                self._decompose_expr(node.target.value)
            elif isinstance(node.target, ast.Subscript):
                self._decompose_expr(node.target.value)
                self._decompose_expr(node.target.slice)
            return
        rhs_dependencies = self._decompose_expr(node.value)
        self._assign_target(
            node.target,
            rhs_dependencies,
            span=self._span(node),
            annotation_types=annotation_types,
        )

    def visit_AugAssign(self, node: ast.AugAssign):
        previous_reference = None
        previous_value: list[str | Reference]
        if isinstance(node.target, _REFERENCE_TYPES):
            previous_reference = self._add_reference_node(
                node.target,
                AccessMode.READ,
            )
            assert previous_reference.reference is not None
            previous_value = [previous_reference.reference]
        elif isinstance(node.target, ast.Name):
            previous_value = self._decompose_expr(
                ast.Name(id=node.target.id, ctx=ast.Load()),
            )
        else:
            previous_value = self._decompose_expr(node.target)
        dependencies = self._decompose_expr(node.value)
        operation_start = len(self.current.nodes)
        self._assign_target(
            node.target,
            dependencies,
            augmented=True,
            augmented_value=previous_value,
            previous_reference=previous_reference,
        )
        for operation in self.current.nodes[operation_start:]:
            if operation.kind == NodeKind.OPERATION:
                operation.display_name = ast.unparse(node)

    def visit_Expr(self, node: ast.Expr):
        self._decompose_expr(node.value)

    def visit_If(self, node: ast.If):
        condition = self._capture_condition(node.test, prefix='if')
        base = list(self._condition_stack)
        base_branches = self._branch_context
        self._branch_context = base_branches | {(condition, True)}
        saved_environment = self._binding_environment
        entry_environment = self._capture_bindings()
        self._binding_environment = entry_environment
        body_conditions = self._visit_in_condition(condition, node.body)
        self._branch_context = base_branches | {(condition, False)}
        self._binding_environment = entry_environment.advance(len(self.current.nodes))
        try:
            else_conditions = self._visit_in_condition(condition, node.orelse)
        finally:
            self._binding_environment = saved_environment
        self._branch_context = base_branches
        body_terminates = self._suite_always_exits(node.body)
        else_terminates = bool(node.orelse) and self._suite_always_exits(node.orelse)

        if body_terminates and else_terminates:
            fallthrough = []
        elif body_terminates or else_terminates:
            fallthrough = [condition, *(body_conditions or else_conditions)]
        else:
            fallthrough = [*body_conditions, *else_conditions]

        self._condition_stack = base
        self._condition_stack.extend(fallthrough)

    def visit_While(self, node: ast.While):
        condition = self._capture_condition(node.test)
        self._visit_in_condition(condition, node.body)
        self._visit_in_condition(condition, node.orelse)

    def visit_For(self, node: ast.For):
        self._visit_for(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._visit_for(node, async_iteration=True)

    def _visit_for(self, node: ast.For | ast.AsyncFor, async_iteration: bool = False):
        iter_dependencies = self._decompose_expr(node.iter)
        if async_iteration:
            iteration_name = self._create_fresh_reference('async_iter')
            self._append_node(
                NodeRecord(
                    name=iteration_name.description,
                    reference=iteration_name,
                    scope=self.current,
                    kind=NodeKind.OPERATION,
                    operation_type=OperationType.TRANSFORM,
                    is_computation=True,
                    inputs=collect_inputs(list(iter_dependencies), AccessMode.READ),
                    span=self._span(node.iter),
                    display_name='async iteration',
                )
            )
            iter_dependencies = [iteration_name]
        condition = self._capture_condition_deps(
            iter_dependencies,
            span=self._span(node.iter),
            display_name=(
                f"{'async ' if async_iteration else ''}for "
                f'{ast.unparse(node.target)} in {ast.unparse(node.iter)}'
            ),
        )
        base_conditions = list(self._condition_stack)
        self._condition_stack.append(condition)
        try:
            target_bindings = self._assign_iteration_target(
                node.target, node.iter, iter_dependencies, span=self._span(node),
            )
            self._condition_stack = base_conditions
            self._visit_in_condition(condition, node.body)
        finally:
            self._condition_stack = base_conditions
        for binding in target_bindings:
            binding.binding_uncertainty_start = len(self.current.nodes)
        self._visit_in_condition(condition, node.orelse)

    def visit_Try(self, node: ast.Try | ast.TryStar):
        saved_interruptions = self._interrupted_scopes
        self._interrupted_scopes |= {self.current}
        enclosing_conditions = list(self._condition_stack)
        body_start, type_event_starts = self._capture_binding_checkpoint()
        output_start = len(self.current.outputs)
        child_start = len(self.current.children)
        saved_environment = self._binding_environment
        self._visit_statements(node.body)
        successful_body_environment = self._capture_bindings()
        body_conditions = self._condition_stack[len(enclosing_conditions):]
        self._condition_stack = list(enclosing_conditions)
        body_nodes = self.current.nodes[body_start:]
        body_dependencies: list[str | Reference] = []
        for record in self._collect_try_computations(
            body_nodes, self.current.children[child_start:]
        ):
            assert record.reference is not None
            body_dependencies.append(record.reference)
        exception_condition = None
        if node.handlers:
            # Dispatch gates type evaluation separately from handler matching.
            exception_condition = self._capture_condition_deps(
                body_dependencies, span=self._span(node), display_name='exception',
            )
            assert exception_condition.reference is not None
            self._preserve_interrupted_bindings(
                body_start, type_event_starts,
                (node.handlers[0].lineno, node.handlers[0].col_offset),
            )
            for record in body_nodes:
                if record.binding is not None or record.output_type in (
                    OutputType.RETURN, OutputType.YIELD,
                ):
                    record.predicates.append(exception_condition)
                    record.inputs.append(DependencyInput(
                        exception_condition.reference, None, is_predicate=True,
                    ))
            previous_condition = exception_condition
            dispatch_environment = self._capture_bindings()
            base_branches = self._branch_context
            skipped_handlers: frozenset[tuple[NodeRecord, bool]] = frozenset()
            for handler in node.handlers:
                # Only except* dispatch can observe earlier handler-body bindings.
                base_conditions = self._condition_stack
                self._binding_environment = dispatch_environment.advance(len(self.current.nodes))
                self._branch_context = (
                    base_branches | skipped_handlers | {(exception_condition, True)}
                )
                self._condition_stack = [*base_conditions, previous_condition]
                type_start = len(self.current.nodes)
                type_conditions = set(self._condition_stack)
                try:
                    handler_type_dependencies = (
                        self._decompose_expr(handler.type) if handler.type is not None else []
                    )
                finally:
                    self._condition_stack = base_conditions
                for binding in self.current.nodes[type_start:]:
                    binding.binding_conditions[:] = [
                        predicate for predicate in binding.binding_conditions
                        if predicate not in type_conditions
                    ]
                assert previous_condition.reference is not None
                condition = self._capture_condition_deps(
                    [previous_condition.reference, *handler_type_dependencies],
                    span=self._span(handler),
                    display_name=(
                        ast.unparse(handler.type)
                        if handler.type is not None
                        else 'exception'
                    ),
                )
                dispatch_environment = self._capture_bindings()
                if isinstance(node, ast.Try):
                    self._branch_context |= {(condition, True)}
                try:
                    self._visit_exception_handler(handler, condition)
                finally:
                    self._branch_context = base_branches
                if isinstance(node, ast.Try):
                    skipped_handlers |= {(condition, False)}
                else:
                    dispatch_environment = self._capture_bindings()
                previous_condition = condition
            self._binding_environment = saved_environment
        if node.orelse and exception_condition is not None:
            self._condition_stack = [*enclosing_conditions, *body_conditions]
            else_output_start = len(self.current.outputs)
            saved_branches = self._branch_context
            self._binding_environment = successful_body_environment.advance(len(self.current.nodes))
            self._branch_context |= {(exception_condition, False)}
            try:
                self._visit_in_condition(exception_condition, node.orelse)
            finally:
                self._binding_environment = saved_environment
                self._branch_context = saved_branches
            if self._suite_always_exits(node.body):
                self.current.outputs[else_output_start:] = [
                    output for output in self.current.outputs[else_output_start:]
                    if output.output_type != OutputType.RETURN
                ]
        assert node.end_lineno is not None and node.end_col_offset is not None
        type_join = (
            (node.finalbody[0].lineno, node.finalbody[0].col_offset)
            if node.finalbody else (node.end_lineno, node.end_col_offset)
        )
        self._preserve_interrupted_bindings(body_start, type_event_starts, type_join)
        self._condition_stack = list(enclosing_conditions)
        final_output_start = len(self.current.outputs)
        self._interrupted_scopes = saved_interruptions
        self._visit_statements(node.finalbody)
        exits = self._suite_always_exits(node.finalbody)
        if not node.handlers and not exits and not self._suite_always_exits(node.body):
            self._condition_stack.extend(body_conditions)
        if exits:
            # A final exit overrides pending returns, but values yielded
            # before entering finally have already been emitted.
            self.current.outputs[output_start:final_output_start] = [
                output
                for output in self.current.outputs[output_start:final_output_start]
                if output.output_type == OutputType.YIELD
            ]


    visit_TryStar = visit_Try

    @staticmethod
    def _collect_try_computations(
        nodes: list[NodeRecord], children: list[ScopeRecord],
    ) -> list[NodeRecord]:
        computations = [node for node in nodes if node.is_computation]
        pending = list(reversed(children))
        while pending:
            scope = pending.pop()
            if scope.kind == ScopeKind.FUNCTION or scope.is_lazy_comprehension:
                continue
            computations.extend(node for node in scope.nodes if node.is_computation)
            pending.extend(reversed(scope.children))
        return computations

    @staticmethod
    def _suite_always_exits(statements: list[ast.stmt]) -> bool:
        for statement in statements:
            if isinstance(statement, (ast.Return, ast.Raise)):
                return True
            if isinstance(statement, ast.If) and statement.orelse:
                if (
                    ScopeBuilder._suite_always_exits(statement.body)
                    and ScopeBuilder._suite_always_exits(statement.orelse)
                ):
                    return True
            if isinstance(statement, (ast.Try, ast.TryStar)):
                if ScopeBuilder._suite_always_exits(statement.finalbody):
                    return True
                handlers_exit = all(
                    ScopeBuilder._suite_always_exits(handler.body)
                    for handler in statement.handlers
                )
                if handlers_exit and (
                    ScopeBuilder._suite_always_exits(statement.body)
                    or ScopeBuilder._suite_always_exits(statement.orelse)
                ):
                    return True
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                # An entered manager can suppress failures in its target
                # assignment or in the setup of a later manager.
                if len(statement.items) != 1:
                    continue
                target = statement.items[0].optional_vars
                if target is not None and not isinstance(target, ast.Name):
                    continue
                if ScopeBuilder._suite_always_returns(statement.body):
                    return True
        return False

    @staticmethod
    def _suite_always_returns(statements: list[ast.stmt]) -> bool:
        potentially_raising_statements = (
            ast.Assert,
            ast.AsyncFor,
            ast.AsyncWith,
            ast.AugAssign,
            ast.ClassDef,
            ast.Delete,
            ast.For,
            ast.Import,
            ast.ImportFrom,
            ast.Match,
            ast.Raise,
            ast.Try,
            ast.TryStar,
            ast.While,
            ast.With,
        )
        for statement in statements:
            if any(
                isinstance(node, potentially_raising_statements)
                or (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and bool(node.decorator_list)
                )
                # Name lookup can raise NameError or UnboundLocalError;
                # this syntax-only check does not prove definite assignment.
                or (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load))
                # Unpacking invokes iteration; truth testing may invoke
                # __bool__ or __len__, even without an explicit call node.
                or (
                    isinstance(node, (ast.Tuple, ast.List))
                    and isinstance(node.ctx, ast.Store)
                )
                or (
                    isinstance(node, ast.If)
                    and not isinstance(node.test, ast.Constant)
                )
                or (
                    isinstance(node, ast.expr)
                    and not isinstance(
                        node, (ast.Name, ast.Constant, ast.Tuple, ast.List)
                    )
                )
                for node in ast.walk(statement)
            ):
                return False
            if isinstance(statement, ast.Return):
                return True
            if isinstance(statement, ast.If):
                if statement.orelse and (
                    ScopeBuilder._suite_always_returns(statement.body)
                    and ScopeBuilder._suite_always_returns(statement.orelse)
                ):
                    return True
        return False

    def visit_With(self, node: ast.With | ast.AsyncWith):
        enclosing_conditions = list(self._condition_stack)
        protected_start, type_event_starts = self._capture_binding_checkpoint()
        for index, item in enumerate(node.items):
            ctx_deps = self._decompose_expr(item.context_expr)
            if item.optional_vars is not None:
                entry_name = self._create_fresh_reference('context_entry')
                self._append_node(
                    NodeRecord(
                        name=entry_name.description,
                        reference=entry_name,
                        scope=self.current,
                        kind=NodeKind.OPERATION,
                        operation_type=OperationType.TRANSFORM,
                        is_computation=True,
                        inputs=collect_inputs(ctx_deps, AccessMode.READ),
                        span=self._span(item.context_expr),
                        display_name='context entry result',
                    )
                )
                if index == 0:
                    protected_start = len(self.current.nodes)
                self._assign_target(item.optional_vars, [entry_name])
            elif ctx_deps:
                with_name = self._create_fresh_reference('with')
                self._append_node(
                    NodeRecord(
                        name=with_name.description,
                        reference=with_name,
                        scope=self.current,
                        is_computation=True,
                        inputs=collect_inputs(ctx_deps, AccessMode.READ),
                    )
                )
            if index == 0 and (
                item.optional_vars is None or isinstance(item.optional_vars, ast.Name)
            ):
                # The first manager cannot suppress its own failed entry.
                # Unpacking its target and entering later managers can be suppressed.
                protected_start = len(self.current.nodes)
        saved_interruptions = self._interrupted_scopes
        self._interrupted_scopes |= {self.current}
        self._visit_statements(node.body)
        self._interrupted_scopes = saved_interruptions

        assert node.end_lineno is not None and node.end_col_offset is not None
        self._preserve_interrupted_bindings(
            protected_start, type_event_starts, (node.end_lineno, node.end_col_offset),
        )
        self._condition_stack = enclosing_conditions

    visit_AsyncWith = visit_With

    def _preserve_interrupted_bindings(
        self, start: int, type_event_starts: dict[NodeRecord, int], type_join: tuple[int, int],
    ) -> None:
        self._merge_annotation_updates(type_event_starts, type_join)
        join = len(self.current.nodes)
        for node in self.current.nodes[start:]:
            if node.binding is None and not node.is_deletion:
                continue
            if node.binding_uncertainty_start is None:
                node.binding_uncertainty_start = join
            else:
                node.binding_uncertainty_start = min(node.binding_uncertainty_start, join)

    def _visit_exception_handler(
        self, node: ast.ExceptHandler, condition: NodeRecord,
    ) -> None:
        body_start, type_event_starts = self._capture_binding_checkpoint()
        if node.name:
            binding_start = len(self.current.bindings.get(node.name, []))
            assert condition.reference is not None
            binding = self._add_bound_node(node.name, [condition.reference])
            binding.predicates.append(condition)
            binding.binding_conditions.clear()
        try:
            self._visit_in_condition(condition, node.body)
        finally:
            assert node.end_lineno is not None and node.end_col_offset is not None
            self._preserve_interrupted_bindings(
                body_start, type_event_starts, (node.end_lineno, node.end_col_offset),
            )
            if node.name:
                visibility_end = len(self.current.nodes)
                for version in self.current.bindings[node.name][binding_start:]:
                    if version.binding_visibility_end is None:
                        version.binding_visibility_end = visibility_end
                    else:
                        version.binding_visibility_end = min(
                            version.binding_visibility_end, visibility_end
                        )

    def visit_Match(self, node: ast.Match):
        subject_dependencies = self._decompose_expr(node.subject)
        previous_case_failure = None
        fallthrough_conditions = []
        saved_environment = self._binding_environment
        dispatch_environment = self._capture_bindings()
        base_branches = self._branch_context
        skipped_cases: frozenset[tuple[NodeRecord, bool]] = frozenset()
        for index, case in enumerate(node.cases):
            self._branch_context = base_branches | skipped_cases
            case_environment = dispatch_environment
            self._binding_environment = case_environment.advance(len(self.current.nodes))
            base_conditions = self._condition_stack
            if previous_case_failure is not None:
                self._condition_stack = [*base_conditions, previous_case_failure]
            try:
                pattern_names, pattern_dependencies = self._pattern_data(case.pattern)
            finally:
                self._condition_stack = base_conditions
            condition_dependencies = [*subject_dependencies, *pattern_dependencies]
            if previous_case_failure is not None:
                assert previous_case_failure.reference is not None
                condition_dependencies.insert(0, previous_case_failure.reference)
            pattern_condition = self._capture_condition_deps(
                condition_dependencies,
                span=self._span(case.pattern),
            )
            assert pattern_condition.reference is not None
            capture_bindings = []
            for name in pattern_names:
                binding = self._add_bound_node(name, [pattern_condition.reference])
                binding.predicates.append(pattern_condition)
                binding.binding_conditions.clear()
                capture_bindings.append(binding)

            condition = pattern_condition
            guard_bindings = []
            if case.guard is not None:
                guard_start = len(self.current.nodes)
                base_conditions = self._condition_stack
                self._condition_stack = [*base_conditions, pattern_condition]
                try:
                    guard_dependencies = self._decompose_expr(case.guard)
                finally:
                    self._condition_stack = base_conditions
                guard_bindings = [
                    binding for binding in self.current.nodes[guard_start:]
                    if binding.binding is not None
                ]
                for binding in guard_bindings:
                    binding.binding_conditions[:] = [
                        predicate for predicate in binding.binding_conditions
                        if predicate is not pattern_condition
                    ]
                condition = self._capture_condition_deps(
                    [pattern_condition.reference, *guard_dependencies],
                    span=self._span(case.guard),
                )
            guard_environment = self._capture_bindings()
            self._branch_context |= {(condition, True)}
            nested_conditions = self._visit_in_condition(condition, case.body)
            self._branch_context = base_branches | skipped_cases
            dispatch_environment = case_environment.merge(
                guard_environment, len(self.current.nodes),
            )
            for binding in [*capture_bindings, *guard_bindings]:
                join = len(self.current.nodes)
                binding.binding_uncertainty_start = (
                    join if binding.binding_uncertainty_start is None
                    else min(binding.binding_uncertainty_start, join)
                )
            if self._suite_always_exits(case.body):
                fallthrough_conditions.append(condition)
            else:
                fallthrough_conditions.extend(nested_conditions)
            skipped_cases |= {(condition, False)}
            if index < len(node.cases) - 1:
                assert condition.reference is not None
                previous_case_failure = self._capture_condition_deps(
                    [condition.reference],
                    span=self._span(case.pattern),
                    display_name='case failure',
                )
        self._branch_context = base_branches
        self._binding_environment = saved_environment
        self._condition_stack.extend(fallthrough_conditions)

    def _visit_in_condition(
        self,
        condition: NodeRecord,
        statements: list[ast.stmt],
    ) -> list[NodeRecord]:
        base = list(self._condition_stack)
        self._condition_stack = [*base, condition]
        binding_start, type_event_starts = self._capture_binding_checkpoint()
        self._visit_statements(statements)
        if statements:
            last = statements[-1]
            assert last.end_lineno is not None and last.end_col_offset is not None
            self._merge_annotation_updates(
                type_event_starts, (last.end_lineno, last.end_col_offset),
            )
        join = len(self.current.nodes)
        for binding in self.current.nodes[binding_start:]:
            if binding.binding is None:
                continue
            binding.binding_uncertainty_start = (
                join if binding.binding_uncertainty_start is None
                else min(binding.binding_uncertainty_start, join)
            )
        nested = self._condition_stack[len(base) + 1 :]
        self._condition_stack = base
        return [] if self._suite_always_exits(statements) else nested

    def _capture_binding_checkpoint(self) -> tuple[int, dict[NodeRecord, int]]:
        """Capture node and annotation-history positions for a suite's updates."""
        return len(self.current.nodes), {
            binding: len(binding.inferred_type_events)
            for binding in self.current.nodes if binding.inferred_type_events
        }

    def _merge_annotation_updates(
        self, type_event_starts: dict[NodeRecord, int], type_join: tuple[int, int],
    ) -> None:
        for binding in self.current.nodes:
            for index in range(type_event_starts.get(binding, 0), len(binding.inferred_type_events)):
                span, hints, merge_from, branches = binding.inferred_type_events[index]
                merge_from = min(merge_from, type_join) if merge_from is not None else type_join
                binding.inferred_type_events[index] = (span, hints, merge_from, branches)

    def _visit_statements(self, statements: list[ast.stmt]) -> None:
        exited = False
        for statement in statements:
            entry_conditions = set(self._condition_stack)
            binding_start = len(self.current.nodes)
            output_start = len(self.current.outputs)
            self.visit(statement)
            for binding in self.current.nodes[binding_start:]:
                if binding.binding is None:
                    continue
                binding.binding_conditions[:] = [
                    predicate for predicate in binding.binding_conditions
                    if predicate not in entry_conditions
                ]
            if exited:
                # Keep written operations and generator identity, but do not
                # supply an unreachable return value to callers.
                self.current.outputs[output_start:] = [
                    output for output in self.current.outputs[output_start:]
                    if output.output_type != OutputType.RETURN
                ]
            else:
                exited = self._suite_always_exits([statement])

    def _pattern_data(
        self, pattern: ast.pattern
    ) -> tuple[list[str], list[str | Reference]]:
        names: list[str] = []
        dependencies: list[str | Reference] = []
        if isinstance(pattern, (ast.MatchAs, ast.MatchStar)):
            name = pattern.name
            if name and name != '_':
                names.append(name)
        elif (
            isinstance(pattern, ast.MatchMapping)
            and pattern.rest
            and pattern.rest != '_'
        ):
            names.append(pattern.rest)

        if isinstance(pattern, ast.MatchValue):
            dependencies.extend(self._decompose_expr(pattern.value))
        elif isinstance(pattern, ast.MatchClass):
            dependencies.extend(self._decompose_expr(pattern.cls))
        elif isinstance(pattern, ast.MatchMapping):
            for key in pattern.keys:
                dependencies.extend(self._decompose_expr(key))

        for child in ast.iter_child_nodes(pattern):
            if isinstance(child, ast.pattern):
                child_names, child_dependencies = self._pattern_data(child)
                names.extend(child_names)
                dependencies.extend(child_dependencies)
        return list(dict.fromkeys(names)), dependencies

    def visit_Raise(self, node: ast.Raise):
        dependencies = self._record_expression_sequence(
            [expression for expression in (node.exc, node.cause) if expression is not None]
        )
        reference = self._create_fresh_reference('raise')
        self._append_node(
            NodeRecord(
                name=reference.description,
                reference=reference,
                scope=self.current,
                kind=NodeKind.OPERATION,
                operation_type=OperationType.RAISE,
                is_computation=True,
                inputs=collect_inputs(dependencies, AccessMode.READ),
                span=self._span(node),
                display_name=ast.unparse(node),
            )
        )

    def visit_Assert(self, node: ast.Assert):
        condition = self._capture_condition(node.test)
        assert condition.reference is not None
        dependencies: list[str | Reference] = [condition.reference]
        if node.msg is not None:
            # Branch polarity is not represented, so later reads retain both
            # the prior value and message writes as alternatives.
            message_condition = self._capture_condition_deps(
                [condition.reference], span=self._span(node.test)
            )
            base_conditions = self._condition_stack
            self._condition_stack = [*base_conditions, message_condition]
            try:
                dependencies.extend(self._decompose_expr(node.msg))
            finally:
                self._condition_stack = base_conditions
        reference = self._create_fresh_reference('assert')
        self._append_node(
            NodeRecord(
                name=reference.description,
                reference=reference,
                scope=self.current,
                kind=NodeKind.OPERATION,
                operation_type=OperationType.ASSERT,
                is_computation=True,
                inputs=collect_inputs(dependencies, AccessMode.READ),
                span=self._span(node),
                display_name=ast.unparse(node),
            )
        )
        self._condition_stack.append(condition)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            binding = alias.asname or alias.name.split('.')[0]
            imported_name = alias.name if alias.asname else binding
            self._record_import(binding, imported_name, span=self._span(node))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == '*':
                imported_name = '.' * node.level
                imported_name += f'{node.module}.*' if node.module else '*'
                imported = self._add_bound_node(
                    self._create_fresh_reference('star_import'),
                    [imported_name],
                    span=self._span(node),
                    bind=False,
                    display_name=f'from {"." * node.level}{node.module or ""} import *',
                )
                imported.is_import = True
                continue
            binding = alias.asname or alias.name
            imported_name = '.' * node.level
            imported_name += f'{node.module}.{alias.name}' if node.module else alias.name
            self._record_import(binding, imported_name, span=self._span(node))

    def _record_import(
        self,
        name: str,
        imported_name: str,
        span: tuple[int, int, int, int],
    ) -> None:
        imported = self._add_bound_node(name, span=span)
        imported.is_import = True
        targets = self.root.bindings.get(imported_name)
        if targets is None:
            target = NodeRecord(
                imported_name, self.root, kind=NodeKind.IMPORT_TARGET,
                binding=imported_name,
            )
            self.root.nodes.append(target)
            targets = self.root.bindings[imported_name] = [target]
        imported.add_dependency(targets[0], access=AccessMode.READ)

    def visit_Return(self, node: ast.Return):
        if node.value:
            self._add_return(node.value, span=self._span(node))
        else:
            self._add_none_return(span=self._span(node))

    def _add_return(
        self,
        rhs: ast.expr,
        span: tuple[int, int, int, int] | None = None,
    ) -> NodeRecord:
        dependencies = self._decompose_expr(rhs)
        output = self._add_bound_node(
            self._allocate_return_name(),
            dependencies,
            span=span,
            bind=False,
            output_type=OutputType.RETURN,
        )
        output.display_name = f'return {ast.unparse(rhs)}'
        self.current.outputs.append(output)
        return output

    def _add_none_return(
        self,
        span: tuple[int, int, int, int] | None = None,
    ) -> NodeRecord:
        output = self._add_bound_node(
            self._allocate_return_name(),
            span=span,
            bind=False,
            output_type=OutputType.RETURN,
            display_name='return None (implicit)' if span is None else 'return',
        )
        self.current.outputs.append(output)
        return output

    def _decompose_call(self, expr: ast.Call) -> list[str | Reference]:
        dep_names: list[str | Reference] = []
        receiver_dependencies: list[str | Reference] = []
        callee = ast.unparse(expr.func)
        callee_dependencies = self._decompose_expr(expr.func)
        if isinstance(expr.func, ast.Attribute):
            attribute_reference = next(
                (node for node in self.current.nodes if node.reference in callee_dependencies),
                None,
            )
            if attribute_reference is not None:
                receiver_dependencies = [
                    occurrence.source or occurrence.name
                    for occurrence in attribute_reference.inputs
                    if not occurrence.is_structural and not occurrence.is_predicate
                ]

        for arg in expr.args:
            dep_names.extend(self._decompose_expr(arg))
        for kw in expr.keywords:
            dep_names.extend(self._decompose_expr(kw.value))

        call_name = self._create_fresh_reference(f'call_{callee}')
        super_expression = (
            expr
            if isinstance(expr.func, ast.Name) and expr.func.id == 'super'
            else expr.func.value
            if isinstance(expr.func, ast.Attribute)
            and isinstance(expr.func.value, ast.Call)
            and isinstance(expr.func.value.func, ast.Name)
            and expr.func.value.func.id == 'super'
            else None
        )
        is_super_call = (
            super_expression is not None
            and not super_expression.args
            and not super_expression.keywords
        )
        super_member = (
            expr.func.attr
            if is_super_call and isinstance(expr.func, ast.Attribute)
            else None
        )
        self._append_node(
            NodeRecord(
                name=call_name.description,
                reference=call_name,
                scope=self.current,
                kind=NodeKind.CALL,
                is_computation=True,
                raw_calls=[callee],
                display_name=ast.unparse(ast.Call(func=expr.func, args=[], keywords=[])),
                inputs=(
                    collect_inputs(callee_dependencies, AccessMode.READ, is_callee=True)
                    + collect_inputs(dep_names, AccessMode.READ, is_call_argument=True)
                ),
                raw_receiver_deps=receiver_dependencies,
                is_dynamic_call=not isinstance(expr.func, (ast.Name, ast.Attribute)),
                is_super_call=is_super_call,
                super_member=super_member,
                span=self._span(expr),
            )
        )
        return [call_name]

    def _decompose_operator(self, expr: ast.expr) -> list[str | Reference]:
        if isinstance(expr, ast.Compare):
            base_stack = self._condition_stack
            base_conditions = list(base_stack)
            branch_conditions: list[NodeRecord] = []
            dependencies = self._decompose_expr(expr.left)
            previous_operation: Reference | None = None
            try:
                for index, comparator in enumerate(expr.comparators, 1):
                    if previous_operation is not None:
                        self._condition_stack = [
                            *base_conditions,
                            *branch_conditions,
                        ]
                        branch_conditions.append(
                            self._capture_condition_deps([previous_operation])
                        )
                    self._condition_stack = [
                        *base_conditions,
                        *branch_conditions,
                    ]
                    comparator_dependencies = self._decompose_expr(comparator)
                    previous_operation = self._add_operator(
                        dependencies + comparator_dependencies,
                        self._span(expr),
                        display_name=ast.unparse(ast.Compare(
                            left=expr.left, ops=expr.ops[:index],
                            comparators=expr.comparators[:index],
                        )),
                    )
                    dependencies = comparator_dependencies
                assert previous_operation is not None  # Comparisons have at least one comparator.
                return [previous_operation]
            finally:
                self._condition_stack = base_stack
        return [
            self._add_operator(
                self._decompose_children(expr),
                self._span(expr),
                display_name=ast.unparse(expr),
            )
        ]

    def _decompose_children(self, expr: ast.expr) -> list[str | Reference]:
        dependencies: list[str | Reference] = []
        if isinstance(expr, ast.Dict):
            for key, value in zip(expr.keys, expr.values):
                if key is not None:
                    dependencies.extend(self._decompose_expr(key))
                dependencies.extend(self._decompose_expr(value))
            return dependencies
        for child in ast.iter_child_nodes(expr):
            if isinstance(child, ast.expr):
                dependencies.extend(self._decompose_expr(child))
        return dependencies

    def _decompose_expr(self, expr: ast.expr) -> list[str | Reference]:
        """Walk an expression, recording data items and returning its dependencies."""
        match expr:
            case ast.Call():
                return self._decompose_call(expr)
            case ast.Lambda():
                lam_name = self._create_fresh_reference('lambda')
                declaration = self._add_bound_node(
                    lam_name,
                    self._record_defaults(expr.args),
                    span=self._span(expr),
                    bind=False,
                )
                saved_conditions = self._condition_stack
                saved_branches = self._branch_context
                saved_environment = self._binding_environment
                self._condition_stack = []
                self._branch_context = frozenset()
                self._binding_environment = None
                try:
                    declaration.declared_scope = self._push(
                        ScopeRecord(
                            name=lam_name.description, symbol=lam_name, kind=ScopeKind.FUNCTION
                        )
                    )
                    self._record_scope_bindings(expr, self.current)
                    self._process_args(expr.args)
                    self._add_return(expr.body, span=self._span(expr))
                finally:
                    self._pop()
                    self._condition_stack = saved_conditions
                    self._branch_context = saved_branches
                    self._binding_environment = saved_environment
                return [lam_name]
            case ast.NamedExpr():
                val_deps = self._decompose_expr(expr.value)
                return [
                    self._assign_named_expression(
                        expr.target, val_deps, span=self._span(expr)
                    )
                ]
            case ast.BoolOp():
                return self._decompose_conditional_bool_op(expr)
            case ast.IfExp():
                return self._decompose_conditional_if_expression(expr)
            case ast.Compare():
                return self._decompose_operator(expr)
            case (
                ast.BinOp()
                | ast.BoolOp()
                | ast.IfExp()
                | ast.UnaryOp()
                | ast.JoinedStr()
                | ast.TemplateStr()
                | ast.Starred()
            ):
                return self._decompose_operator(expr)
            case ast.Yield() | ast.YieldFrom() | ast.Await():
                prefix = 'yield' if isinstance(expr, _YIELD_TYPES) else 'await'
                dependencies = (
                    self._decompose_expr(expr.value) if expr.value is not None else []
                )
                yield_display_name = None
                if isinstance(expr, ast.Yield):
                    yield_display_name = (
                        f'yield {ast.unparse(expr.value)}'
                        if expr.value is not None
                        else 'yield'
                    )
                elif isinstance(expr, ast.YieldFrom):
                    yield_display_name = (
                        f'yield from {ast.unparse(expr.value)}'
                    )
                output = self._add_bound_node(
                    self._create_fresh_reference(prefix),
                    dependencies,
                    span=self._span(expr),
                    bind=False,
                    output_type=(
                        OutputType.YIELD
                        if isinstance(expr, _YIELD_TYPES)
                        else OutputType.RESULT
                    ),
                    display_name=yield_display_name,
                )
                output.is_computation = isinstance(expr, ast.Await)
                if isinstance(expr, _YIELD_TYPES):
                    self.current.outputs.append(output)
                if isinstance(expr, ast.Yield):
                    result_dependencies = []
                    result_prefix = 'yield_result'
                elif isinstance(expr, ast.YieldFrom):
                    result_dependencies = dependencies
                    result_prefix = 'yield_from_result'
                else:
                    assert output.reference is not None
                    return [output.reference]
                result = self._add_bound_node(
                    self._create_fresh_reference(result_prefix),
                    result_dependencies,
                    span=self._span(expr),
                    bind=False,
                    output_type=OutputType.RESULT,
                    display_name=(
                        'yield (received)'
                        if isinstance(expr, ast.Yield)
                        else 'yield from result'
                        if isinstance(expr, ast.YieldFrom)
                        else None
                    ),
                )
                if isinstance(expr, ast.YieldFrom):
                    result.kind = NodeKind.YIELD_FROM_RESULT
                    result.is_computation = True
                assert result.reference is not None
                return [result.reference]
            case ast.ListComp() | ast.SetComp() | ast.DictComp() | ast.GeneratorExp():
                return [self._build_comprehension(expr)]
            case ast.List() | ast.Tuple() | ast.Set() | ast.Dict():
                container_name = self._create_fresh_reference('container')
                self._append_node(
                    NodeRecord(
                        name=container_name.description,
                        reference=container_name,
                        scope=self.current,
                        kind=NodeKind.OPERATION,
                        operation_type=OperationType.CONTAINER,
                        is_computation=True,
                        inputs=collect_inputs(self._decompose_children(expr), AccessMode.READ),
                        span=self._span(expr),
                        display_name=ast.unparse(expr),
                    )
                )
                return [container_name]
            case ast.Attribute(ctx=ast.Load()):
                access_deps = self._decompose_expr(expr.value)
                access_name = self._create_fresh_reference('ref')
                self._append_node(
                    NodeRecord(
                        name=access_name.description,
                        reference=access_name,
                        scope=self.current,
                        kind=NodeKind.REFERENCE,
                        is_computation=True,
                        access=AccessMode.READ,
                        inputs=collect_inputs(access_deps, AccessMode.READ),
                        span=self._span(expr),
                        display_name=ast.unparse(expr),
                        attribute_expression=expr,
                    )
                )
                return [access_name]
            case ast.Subscript(ctx=ast.Load()):
                access_deps = self._decompose_expr(expr.value)
                access_deps.extend(self._decompose_expr(expr.slice))
                access_name = self._create_fresh_reference('ref')
                self._append_node(
                    NodeRecord(
                        name=access_name.description,
                        reference=access_name,
                        scope=self.current,
                        kind=NodeKind.SUBSCRIPT,
                        is_computation=True,
                        access=AccessMode.READ,
                        inputs=collect_inputs(access_deps, AccessMode.READ),
                        span=self._span(expr),
                        display_name=ast.unparse(expr),
                        subscript_expression=expr,
                    )
                )
                return [access_name]
            case ast.Name(ctx=ast.Load()):
                if self.current.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION):
                    for binding in self.current.find_nodes(expr.id, position=len(self.current.nodes)):
                        if (
                            binding.scope.type_parameter_bindings.get(expr.id) is binding
                            and self.current not in (binding.scope, binding.scope.parent)
                        ):
                            # Unsupported generic captures remain unresolved in this scope.
                            self.current.defines.add(expr.id)
                read_scope = self.current
                # Eager comprehensions read enclosing values now, rather than
                # using the final bindings of a deferred function body.
                while (
                    read_scope.kind == ScopeKind.COMPREHENSION
                    and not read_scope.is_lazy_comprehension
                    and expr.id not in read_scope.defines
                    and read_scope.parent is not None
                    and read_scope.parent.kind != ScopeKind.CLASS
                ):
                    read_scope = read_scope.parent
                return [Reference(
                    expr.id, read_scope, len(read_scope.nodes),
                    environment=self._capture_bindings(read_scope),
                )]
            case _:
                return self._decompose_children(expr)

    def _decompose_conditional_bool_op(
        self, expr: ast.BoolOp
    ) -> list[str | Reference]:
        base_conditions = list(self._condition_stack)
        branch_conditions: list[NodeRecord] = []
        dependencies: list[str | Reference] = []
        value_sources: list[str | Reference] = []
        previous_dependencies: list[str | Reference] = []
        try:
            for index, value in enumerate(expr.values):
                self._condition_stack = [*base_conditions, *branch_conditions]
                if index:
                    previous_value = ast.unparse(expr.values[index - 1])
                    condition = self._capture_condition_deps(
                        previous_dependencies,
                        display_name=f'{previous_value}?',
                    )
                    branch_conditions.append(condition)
                    self._condition_stack.append(condition)
                previous_dependencies = self._decompose_expr(value)
                dependencies.extend(previous_dependencies)
                value_sources.extend(previous_dependencies)
        finally:
            self._condition_stack = base_conditions
        return [
            self._add_operator(
                dependencies,
                self._span(expr),
                value_sources=value_sources,
                display_name=ast.unparse(expr),
            )
        ]

    def _decompose_conditional_if_expression(
        self, expr: ast.IfExp
    ) -> list[str | Reference]:
        base_conditions = list(self._condition_stack)
        test_dependencies = self._decompose_expr(expr.test)
        condition = self._capture_condition_deps(
            test_dependencies, span=self._span(expr.test)
        )
        saved_environment = self._binding_environment
        entry_environment = self._capture_bindings()
        try:
            self._binding_environment = entry_environment
            self._condition_stack = [*base_conditions, condition]
            body_dependencies = self._decompose_expr(expr.body)
            self._binding_environment = entry_environment.advance(len(self.current.nodes))
            self._condition_stack = [*base_conditions, condition]
            else_dependencies = self._decompose_expr(expr.orelse)
        finally:
            self._condition_stack = base_conditions
            self._binding_environment = saved_environment
        return [
            self._add_operator(
                test_dependencies + body_dependencies + else_dependencies,
                self._span(expr),
                value_sources=body_dependencies + else_dependencies,
            )
        ]

    def _build_comprehension(
        self,
        expr: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp,
    ) -> Reference:
        # First generator's iter is evaluated in the enclosing scope
        iter_deps = self._decompose_expr(expr.generators[0].iter)

        comp_name = self._create_fresh_reference('comp')
        saved_conditions = self._condition_stack
        saved_environment = self._binding_environment
        if isinstance(expr, ast.GeneratorExp):
            self._binding_environment = None
        self._condition_stack = list(saved_conditions)
        comp_scope = self._push(
            ScopeRecord(
                name=comp_name.description,
                symbol=comp_name,
                kind=ScopeKind.COMPREHENSION,
                is_lazy_comprehension=isinstance(expr, ast.GeneratorExp),
                defines={
                    target.id
                    for generator in expr.generators
                    for target in ast.walk(generator.target)
                    if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store)
                },
            )
        )
        for index, generator in enumerate(expr.generators):
            gen_deps = iter_deps if index == 0 else self._decompose_expr(generator.iter)
            iteration_deps = gen_deps
            if generator.is_async:
                async_iteration = self._create_fresh_reference('async_iter')
                iteration_scope = (
                    comp_scope.parent
                    if index == 0 and comp_scope.is_lazy_comprehension
                    else comp_scope
                )
                assert iteration_scope is not None  # Comprehensions have an enclosing scope.
                self.current = iteration_scope
                self._append_node(
                    NodeRecord(
                        name=async_iteration.description,
                        reference=async_iteration,
                        scope=iteration_scope,
                        kind=NodeKind.OPERATION,
                        operation_type=OperationType.TRANSFORM,
                        is_computation=True,
                        inputs=collect_inputs(list(gen_deps), AccessMode.READ),
                        span=self._span(generator.iter),
                        display_name='async iteration',
                    )
                )
                self.current = comp_scope
                iteration_deps = [async_iteration]
            condition = self._capture_condition_deps(
                iteration_deps,
                span=self._span(generator.iter),
                display_name=(
                    f"{'async ' if generator.is_async else ''}for "
                    f'{ast.unparse(generator.target)} in {ast.unparse(generator.iter)}'
                ),
            )
            self._condition_stack.append(condition)
            self._assign_iteration_target(
                generator.target, generator.iter, iteration_deps,
            )
            for cond in generator.ifs:
                self._condition_stack.append(
                    self._capture_condition(cond, prefix='if')
                )

        if isinstance(expr, ast.DictComp):
            key_deps = self._decompose_expr(expr.key)
            val_deps = self._decompose_expr(expr.value)
            returned_node = self._add_bound_node(
                self._allocate_return_name(),
                key_deps + val_deps,
                span=self._span(expr.key),
                bind=False,
                output_type=OutputType.RETURN,
            )
            self.current.outputs.append(returned_node)
        else:
            returned_node = self._add_return(expr.elt, span=self._span(expr.elt))
        returned_node.display_name = ast.unparse(expr)
        returned_node.kind = NodeKind.COMPREHENSION
        returned_node.is_generator_expression = isinstance(expr, ast.GeneratorExp)
        returned_node.is_computation = not returned_node.is_generator_expression
        self._condition_stack = saved_conditions
        self._binding_environment = saved_environment
        self._pop()
        assert returned_node.reference is not None
        return returned_node.reference

    def _assign_iteration_target(
        self, target: ast.expr, iterable: ast.expr,
        dependencies: list[str | Reference],
        span: tuple[int, int, int, int] | None = None,
    ) -> list[NodeRecord]:
        bindings = self._assign_target(
            target,
            [self._add_operator(
                dependencies, self._span(target),
                display_name=f'{ast.unparse(target)} in {ast.unparse(iterable)}',
                operation_type=OperationType.EXTRACT,
            )],
            span=span,
        )
        for binding in bindings:
            binding.binding_conditions.clear()
        return bindings

    def _assign_target(
        self,
        target: ast.expr,
        rhs_dependencies: list[str | Reference],
        span: tuple[int, int, int, int] | None = None,
        augmented: bool = False,
        annotation_types: set[AnnotationHint] | None = None,
        augmented_value: list[str | Reference] | None = None,
        previous_reference: NodeRecord | None = None,
        extraction_display_name: str | None = None,
    ) -> list[NodeRecord]:
        dependencies = rhs_dependencies
        bindings = []
        if isinstance(target, (ast.Tuple, ast.List)):
            dependencies = [self._add_operator(
                dependencies, span,
                display_name=extraction_display_name or ast.unparse(target),
                operation_type=OperationType.EXTRACT,
            )]
            for element in target.elts:
                bindings.extend(self._assign_target(
                    element,
                    dependencies,
                    span,
                    augmented,
                    annotation_types,
                ))
            return bindings
        if isinstance(target, ast.Starred):
            return self._assign_target(
                target.value,
                dependencies,
                span,
                augmented,
                annotation_types,
            )
        if isinstance(target, _REFERENCE_TYPES):
            if augmented:
                previous = previous_reference or self._add_reference_node(
                    target, AccessMode.READ
                )
                assert previous.reference is not None
                operation = self._add_operator(
                    [previous.reference, *dependencies], span
                )
                updated = self._add_reference_node(
                    target, AccessMode.WRITE,
                    [occurrence.source or occurrence.name for occurrence in previous.inputs],
                )
                updated.inputs.append(DependencyInput(operation, AccessMode.READ))
                return []
            reference = self._add_reference_node(target, AccessMode.WRITE)
            reference.inputs.extend(collect_inputs(dependencies, AccessMode.READ))
            return []

        for name in self._target_names(target):
            if name in self.current.global_decls or name in self.current.nonlocal_decls:
                binding = self._add_write_node(
                    name,
                    dependencies,
                    span=span,
                    augmented=augmented,
                    augmented_value=augmented_value,
                )
            else:
                if augmented:
                    inferred_types = set()
                elif annotation_types:
                    inferred_types = set(annotation_types)
                else:
                    inferred_types = self._infer_dependency_types(dependencies)
                write_dependencies = dependencies
                if augmented:
                    previous_value = (
                        augmented_value
                        if augmented_value is not None
                        else [name]
                    )
                    write_dependencies = [
                        self._add_operator([*previous_value, *dependencies])
                    ]
                binding = self._add_bound_node(
                    name,
                    write_dependencies,
                    span=None if augmented else span,
                    dependency_access=AccessMode.READ,
                )
                binding.inferred_types = inferred_types
            bindings.append(binding)
        return bindings

    def _assign_named_expression(
        self,
        target: ast.Name,
        dependencies: list[str | Reference],
        span: tuple[int, int, int, int] | None = None,
    ) -> Reference:
        scope = self.current
        if scope.kind != ScopeKind.COMPREHENSION:
            self._assign_target(target, dependencies, span=span)
            assert self.current.nodes[-1].reference is not None
            return self.current.nodes[-1].reference

        target_scope = scope
        while target_scope.kind == ScopeKind.COMPREHENSION:
            parent = target_scope.parent
            assert parent is not None
            target_scope = parent

        self.current = target_scope
        try:
            self._assign_target(target, dependencies, span=span)
        finally:
            self.current = scope

        reference = target_scope.bindings[target.id][-1].reference
        assert reference is not None
        return reference

    def _add_write_node(
        self,
        root: str,
        dependencies: list[str | Reference],
        lhs: ast.expr | None = None,
        span: tuple[int, int, int, int] | None = None,
        augmented: bool = False,
        augmented_value: list[str | Reference] | None = None,
    ) -> NodeRecord:
        external = (
            root in self.current.global_decls or root in self.current.nonlocal_decls
        )
        target_deps = (
            self._decompose_expr(lhs)
            if isinstance(lhs, (ast.Attribute, ast.Subscript))
            else []
        )
        if augmented:
            previous_value = (
                augmented_value if augmented_value is not None else [root]
            )
            operator = self._add_operator(
                [*previous_value, *target_deps, *dependencies],
            )
            raw_deps: list[str | Reference] = [operator]
        else:
            raw_deps = (
                [*target_deps, *dependencies]
                if external and target_deps
                else dependencies
                if external
                else [*target_deps, *dependencies]
                if target_deps
                else [root, *dependencies]
            )
        write_name = self._create_fresh_reference(f'write_{root}')
        return self._append_node(
            NodeRecord(
                name=write_name.description,
                reference=write_name,
                scope=self.current,
                kind=NodeKind.VARIABLE if external else NodeKind.RESULT,
                access=AccessMode.WRITE,
                binding=root if external else None,
                is_global_write=root in self.current.global_decls,
                is_nonlocal_write=root in self.current.nonlocal_decls,
                target=root,
                inputs=collect_inputs(raw_deps, AccessMode.READ),
                span=span,
            )
        )
    def _add_reference_node(
        self,
        target: ast.Attribute | ast.Subscript,
        access: AccessMode,
        dependencies: list[str | Reference] | None = None,
    ) -> NodeRecord:
        if dependencies is None:
            expressions = [target.value]
            if isinstance(target, ast.Subscript):
                expressions.append(target.slice)
            dependencies = []
            for expression in expressions:
                dependencies.extend(self._decompose_expr(expression))
        kind = (
            NodeKind.SUBSCRIPT
            if isinstance(target, ast.Subscript)
            else NodeKind.REFERENCE
        )
        reference = self._create_fresh_reference('ref')
        return self._append_node(
            NodeRecord(
                name=reference.description,
                reference=reference,
                scope=self.current,
                kind=kind,
                is_computation=True,
                access=access,
                inputs=collect_inputs(list(dependencies), AccessMode.READ),
                span=self._span(target),
                display_name=ast.unparse(target),
                attribute_expression=(
                    target if isinstance(target, ast.Attribute) else None
                ),
            )
        )

    def _capture_condition(
        self, test: ast.expr, prefix: str | None = None
    ) -> NodeRecord:
        """Represent a predicate as an ordinary data transformation node."""
        display_name = ast.unparse(test)
        if prefix is not None:
            display_name = f'{prefix} {display_name}'
        return self._capture_condition_deps(
            self._decompose_expr(test),
            span=self._span(test),
            display_name=display_name,
        )

    def _process_args(self, args: ast.arguments) -> None:
        assert self.current.parent is not None
        regular = args.posonlyargs + args.args
        first_positional = regular[0] if regular else None
        parameters = regular + args.kwonlyargs
        type_parameters = frozenset(self.current.type_parameter_bindings)
        for arg in parameters:
            binding = self._add_bound_node(arg.arg, [])
            binding.is_first_positional_parameter = arg is first_positional
            binding.inferred_types = (
                self._collect_annotation_hints(
                    arg.annotation, self.current.parent, None, type_parameters,
                )
                if arg.annotation else set()
            )
        for variadic_arg in (args.vararg, args.kwarg):
            if variadic_arg is None:
                continue
            # Their annotations describe elements, not the tuple or dict receiver.
            binding = self._add_bound_node(variadic_arg.arg, [])
            binding.is_first_positional_parameter = variadic_arg is first_positional

    def _add_type_parameter_bindings(self, parameters: list[ast.type_param]) -> None:
        for parameter in parameters:
            assert isinstance(parameter, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple))
            name = parameter.name
            is_body_local = name in self.current.defines
            binding = self._add_bound_node(name, [], span=self._span(parameter))
            binding.is_global_write = False
            binding.is_nonlocal_write = False
            self.current.type_parameter_bindings[name] = binding
            if not is_body_local:
                self.current.defines.discard(name)

    @staticmethod
    def _collect_annotation_hints(
        annotation: ast.expr, scope: ScopeRecord, position: int | None,
        type_parameters: frozenset[str] = frozenset(),
        environment: BindingEnvironment | None = None,
    ) -> set[AnnotationHint]:
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            try:
                parsed = ast.parse(annotation.value, mode='eval').body
            except SyntaxError:
                return set()
            if isinstance(parsed, (ast.Name, ast.Attribute)):
                return {AnnotationHint(ast.unparse(parsed), scope, position, type_parameters, environment)}
            return set()
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            return (
                ScopeBuilder._collect_annotation_hints(
                    annotation.left, scope, position, type_parameters, environment,
                )
                | ScopeBuilder._collect_annotation_hints(
                    annotation.right, scope, position, type_parameters, environment,
                )
            )
        if isinstance(annotation, (ast.Name, ast.Attribute, ast.Subscript)):
            return {AnnotationHint(ast.unparse(annotation), scope, position, type_parameters, environment)}
        return set()

    def _infer_dependency_types(self, dependencies: list[str | Reference]) -> set[AnnotationHint]:
        types: set[AnnotationHint] = set()
        for dependency in dependencies:
            source = self._nodes_by_id.get(dependency) if isinstance(dependency, Reference) else None
            if source is not None:
                types.update(source.collect_type_hints())
            elif isinstance(dependency, str):
                for binding in self.current.find_nodes(dependency):
                    types.update(binding.collect_type_hints())
        return types

    def _record_defaults(self, args: ast.arguments) -> list[str | Reference]:
        return self._record_expression_sequence(
            [
                default
                for default in (*args.defaults, *args.kw_defaults)
                if default is not None
            ]
        )

    @staticmethod
    def _span(
        node: ast.stmt | ast.expr | ast.pattern | ast.excepthandler | ast.type_param,
    ) -> tuple[int, int, int, int]:
        # Source nodes come from parsing and carry complete locations.
        return cast(tuple[int, int, int, int], (
            node.lineno,
            node.col_offset,
            getattr(node, 'end_lineno', node.lineno),
            getattr(node, 'end_col_offset', node.col_offset),
        ))

    def _capture_bindings(self, scope: ScopeRecord | None = None) -> BindingEnvironment:
        scope = self.current if scope is None else scope
        conditions = frozenset(self._condition_stack)
        if scope is not self.current:
            # Eager enclosing reads keep their cursor-based approximation.
            context = self._binding_environment
            while context is not None and context.scope is not scope:
                context = context.parent
            return BindingEnvironment(
                scope, context.position if context is not None else 0,
                context.bindings if context is not None else {},
                context.definite_names if context is not None else frozenset(),
                context.parent if context is not None else None, conditions,
                context.type_events if context is not None else {},
            )
        return scope.capture_binding_environment(
            position=len(scope.nodes), active_conditions=conditions,
            environment=self._binding_environment,
        )

    def _push(self, record: ScopeRecord) -> ScopeRecord:
        record.parent = self.current
        self.current.children.append(record)
        self.all_scopes.append(record)
        self.current = record
        return record

    def _pop(self):
        parent = self.current.parent
        assert parent is not None
        self.current = parent

    def _allocate_return_name(self) -> str:
        key = id(self.current)
        index = self._return_counters.get(key, 0)
        self._return_counters[key] = index + 1
        return f'__return_{index}__'

    def _add_operator(
        self,
        dependencies: list[str | Reference],
        span: tuple[int, int, int, int] | None = None,
        value_sources: list[str | Reference] | None = None,
        display_name: str | None = None,
        operation_type: OperationType = OperationType.TRANSFORM,
    ) -> Reference:
        name = self._create_fresh_reference('op')
        self._append_node(
            NodeRecord(
                name=name.description,
                reference=name,
                scope=self.current,
                inputs=collect_inputs(dependencies, AccessMode.READ),
                kind=NodeKind.OPERATION,
                operation_type=operation_type,
                is_computation=operation_type != OperationType.EXTRACT,
                span=span,
                display_name=display_name,
                value_sources=value_sources or [],
            )
        )
        return name

    def _add_bound_node(
        self,
        name: str | Reference,
        raw_deps: list[str | Reference] | None = None,
        span: tuple[int, int, int, int] | None = None,
        bind: bool = True,
        output_type: OutputType | None = None,
        display_name: str | None = None,
        dependency_access: AccessMode | None = AccessMode.READ,
    ) -> NodeRecord:
        binding = None
        if bind:
            assert isinstance(name, str)
            binding = name
        record = NodeRecord(
            name=name.description if isinstance(name, Reference) else name,
            reference=name if isinstance(name, Reference) else Reference(name),
            scope=self.current,
            kind=NodeKind.VARIABLE if bind else NodeKind.RESULT,
            inputs=collect_inputs(raw_deps or [], dependency_access),
            span=span,
            access=AccessMode.WRITE if bind else None,
            binding=binding,
            is_global_write=bind and name in self.current.global_decls,
            is_nonlocal_write=bind and name in self.current.nonlocal_decls,
            target=binding,
            output_type=output_type,
            display_name=display_name,
        )
        if bind:
            self.current.defines.add(
                name.description if isinstance(name, Reference) else name
            )
        return self._append_node(record)

    def _capture_condition_deps(
        self,
        dependencies: list[str | Reference],
        span: tuple[int, int, int, int] | None = None,
        display_name: str | None = None,
    ) -> NodeRecord:
        cond_name = self._create_fresh_reference('cond')
        return self._append_node(
            NodeRecord(
                name=cond_name.description,
                reference=cond_name,
                scope=self.current,
                kind=NodeKind.CONDITION,
                inputs=collect_inputs(dependencies, AccessMode.READ),
                span=span,
                display_name=display_name,
            )
        )

    def _append_node(self, node: NodeRecord) -> NodeRecord:
        """Register an IR item with explicit expression identity."""
        assert node.reference is not None
        node.branch_context = self._branch_context
        for condition in self._condition_stack:
            assert condition.reference is not None
            node.predicates.append(condition)
            if node.binding is not None or node.is_deletion:
                node.binding_conditions.append(condition)
            if condition.reference not in node.raw_deps:
                node.inputs.append(
                    DependencyInput(condition.reference, AccessMode.READ, is_predicate=True)
                )
            else:
                node.inputs[:] = [
                    DependencyInput(
                        occurrence.name, AccessMode.READ,
                        is_structural=occurrence.is_structural,
                        is_predicate=True,
                    )
                    if occurrence.name is condition.reference else occurrence
                    for occurrence in node.inputs
                ]
        if node.binding is not None:
            self.current.bindings.setdefault(node.binding, []).append(node)
        node.scope_position = len(self.current.nodes)
        self.current.nodes.append(node)
        self._nodes_by_id[node.reference] = node
        return node

    def _create_fresh_reference(self, prefix: str) -> Reference:
        while True:
            idx = self._counter
            self._counter += 1
            name = f'__{prefix}_{idx}__'
            if name not in self._source_names:
                return Reference(name)

    def visit_Global(self, node: ast.Global):
        if self.current.kind != ScopeKind.MODULE:
            self.current.global_decls.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        for name in node.names:
            self.current.nonlocal_decls.add(name)
