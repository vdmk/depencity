"""Build completed source IR without exposing intermediate resolution state."""

from __future__ import annotations

import ast
import builtins
from collections.abc import Iterable, Sequence
from dataclasses import replace
from typing import cast

from depencity._graph.model.enums import (
    AccessMode,
    NodeKind,
    OperationType,
    ScopeKind,
)
from depencity._graph.model.ir import (
    AnnotationHint,
    BindingEnvironment,
    DependencyInput,
    NodeRecord,
    ScopeRecord,
)
from depencity._graph.model.reference import Reference
from depencity._graph.scope_builder import _collect_exported_imports, build_ir

_SUPPORTED_CONTAINER_IMPORTS = {
    'builtins.list', 'builtins.tuple',
    'typing.List', 'typing.Tuple', 'typing.Sequence',
    'typing.MutableSequence', 'collections.abc.Sequence',
    'collections.abc.MutableSequence',
}


def build_resolved_ir(tree: ast.Module) -> list[ScopeRecord]:
    """Own source analysis and resolution, returning IR ready for lowering."""
    annotation_names = _collect_annotation_import_names(tree)
    records = build_ir(tree, retained_import_names=annotation_names)
    annotation_imports = {
        node
        for scope in records
        for node in scope.nodes
        if node.is_import and node.binding in annotation_names
    } - _collect_exported_imports(tree, records[1])
    resolve(records)
    remove_resolved_scope_bindings(records)
    finalize_resolved_ir(records, annotation_imports)
    return records


def finalize_resolved_ir(
    records: list[ScopeRecord],
    annotation_imports: set[NodeRecord],
    shadowed_module_members: set[tuple[NodeRecord, str]] | None = None,
) -> None:
    """Finish resolved IR for lowering after declaration cleanup.

    Source and any package-specific resolution must already be complete.
    External targets precede annotation-import pruning, then reads are resolved
    before lexical binding nodes are constructed.
    """
    resolve_external_imports(records, shadowed_module_members)
    _remove_unused_annotation_imports(records, annotation_imports)
    _resolve_builtin_dependencies(records)
    resolve_read_occurrences(records)
    _create_binding_nodes(records)


def _create_binding_nodes(records: list[ScopeRecord]) -> None:
    """Give lexical versions a shared binding in their defining scope.

    Root import targets and unresolved placeholders are not lexical bindings.
    Membership does not participate in source name resolution or value flow.
    Named function and class scopes share the binding of their lexical name.
    """
    bindings: dict[tuple[ScopeRecord, str], NodeRecord] = {}
    type_parameter_bindings: dict[tuple[ScopeRecord, str], NodeRecord] = {}
    for record in records:
        if record.kind == ScopeKind.ROOT:
            continue
        for name, versions in record.bindings.items():
            for version in versions:
                if (
                    version.is_unresolved
                    or version.scope.kind == ScopeKind.ROOT
                    or version.binding_node is not None
                ):
                    continue
                if record.type_parameter_bindings.get(name) is version:
                    version.binding_node = _get_binding_node(type_parameter_bindings, record, name)
                else:
                    owner = version.scope.find_binding_scope(name)
                    version.binding_node = _get_binding_node(bindings, owner, name)
    for record in records:
        if (
            record.kind in (ScopeKind.FUNCTION, ScopeKind.CLASS)
            and isinstance(record.symbol, str)
            and record.parent is not None
        ):
            owner = record.parent.find_binding_scope(record.symbol)
            binding = _get_binding_node(bindings, owner, record.symbol)
            binding.bound_scopes.append(record)


def _get_binding_node(
    bindings: dict[tuple[ScopeRecord, str], NodeRecord],
    owner: ScopeRecord,
    name: str,
) -> NodeRecord:
    key = (owner, name)
    binding = bindings.get(key)
    if binding is None:
        binding = bindings[key] = NodeRecord(
            name=f'__binding_{name}__', scope=owner,
            display_name=name, kind=NodeKind.BINDING,
        )
        owner.nodes.append(binding)
    return binding


def _collect_annotation_import_names(tree: ast.Module) -> set[str]:
    annotations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and node.annotation is not None:
            annotations.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                annotations.append(node.returns)
        elif isinstance(node, ast.AnnAssign):
            annotations.append(node.annotation)
    names = set()
    pending: list[ast.AST] = list(annotations)
    while pending:
        expression = pending.pop()
        if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
            try:
                expression = ast.parse(expression.value, mode='eval')
            except SyntaxError:
                continue
        if isinstance(expression, ast.Name):
            names.add(expression.id)
        pending.extend(ast.iter_child_nodes(expression))
    return names


def _remove_unused_annotation_imports(
    scopes: list[ScopeRecord], annotation_imports: set[NodeRecord]
) -> None:
    pending = [
        node for scope in scopes if scope.kind != ScopeKind.ROOT
        for node in scope.nodes if node not in annotation_imports
    ]
    referenced = set()
    while pending:
        node = pending.pop()
        if id(node) in referenced:
            continue
        referenced.add(id(node))
        pending.extend(
            dependency for dependency in node.deps
            if isinstance(dependency, NodeRecord)
        )
    for node in annotation_imports:
        if id(node) in referenced:
            continue
        scope = node.scope
        scope.nodes.remove(node)
        binding = node.binding
        assert binding is not None  # Annotation imports are named bindings.
        definitions = scope.bindings[binding]
        definitions[:] = [definition for definition in definitions if definition is not node]
        if not definitions:
            del scope.bindings[binding]

    root = scopes[0]
    root.nodes[:] = [node for node in root.nodes if id(node) in referenced]
    root.bindings = {
        name: [node for node in nodes if id(node) in referenced]
        for name, nodes in root.bindings.items()
        if any(id(node) in referenced for node in nodes)
    }


def call_targets(scope: ScopeRecord) -> Sequence[NodeRecord | ScopeRecord]:
    return scope.outputs or [scope]


def _add_call_targets(node: NodeRecord, scope: ScopeRecord) -> None:
    node.inferred_types.update(scope.return_types)
    node.resolved_call_targets.add(scope)
    if (scope.kind == ScopeKind.CLASS or not scope.outputs) and any(
        isinstance(dependency, NodeRecord)
        and (declaration := _find_alias_target(dependency)) is not None
        and declaration.declared_scope is scope
        and (dependency is not declaration or not _is_empty_scope_binding(declaration))
        and any(
            occurrence is not None and occurrence.is_callee
            for occurrence in node.deps[dependency]
        )
        for dependency in node.deps
    ):
        # The declaration or its linear alias supplies the called class value.
        return
    for target in call_targets(scope):
        node.add_dependency(target, access=AccessMode.READ)


def _add_constructor_targets(node: NodeRecord, class_scope: ScopeRecord) -> None:
    if class_scope.kind != ScopeKind.CLASS:
        return
    for binding in _find_class_member_bindings(class_scope, '__init__') or []:
        if binding.declared_scope is not None:
            if not _is_empty_scope_binding(binding):
                node.add_dependency(binding, access=AccessMode.READ)
        elif not any(
            occurrence is not None and occurrence.is_callee
            for occurrence in node.deps.get(binding, {})
        ):
            assert binding.reference is not None  # Class members originate in source.
            node.add_dependency(binding, DependencyInput(
                binding.reference, AccessMode.READ, is_callee=True,
            ))
    initializers = _find_class_member_scopes(class_scope, '__init__')
    for initializer in initializers:
        node.resolved_call_targets.add(initializer)
        for target in call_targets(initializer):
            node.add_dependency(target, access=AccessMode.READ)


def _find_annotation_class(hint: AnnotationHint) -> ScopeRecord | None:
    scope = hint.scope
    parts = hint.parse_class_name()
    if not parts:
        return None
    if (
        parts[0] == '__class__' and scope.kind == ScopeKind.CLASS
        and '__class__' not in scope.global_decls | scope.nonlocal_decls
    ):
        bindings = scope.find_member_nodes('__class__')
        if scope.class_declaration is not None and not any(
            not binding.is_deletion and not scope.is_binding_conditional(binding)
            for binding in bindings
        ):
            bindings = [*bindings, scope.class_declaration]
    else:
        bindings = scope.find_nodes(
            parts[0], position=hint.position, environment=hint.environment,
        )
    if not bindings:
        # Forward hints use final bindings, with the same target and member
        # checks as hints whose root is already visible.
        bindings = scope.find_nodes(parts[0])
    if len(parts) > 1 and _has_direct_member_write(
        scope, bindings, '.'.join(parts), None, position=hint.position,
    ):
        return None
    candidates: list[ScopeRecord] = []
    for binding in bindings:
        if not binding.is_import and not binding.class_object_targets:
            alias = _find_alias_target(binding)
            if alias is not None and alias.is_import:
                binding = alias
        if binding.is_import:
            for dependency in binding.deps:
                if not isinstance(dependency, NodeRecord) or dependency.scope.kind != ScopeKind.ROOT:
                    continue
                origin = _find_import_origin(dependency)
                candidates.extend(
                    target for target in origin.deps
                    if isinstance(target, ScopeRecord) and target.kind == ScopeKind.MODULE
                    and origin.binding == target.name
                )
                if (
                    not origin.deps and origin.binding and len(parts) > 1
                    and not any(
                        module.kind == ScopeKind.MODULE and origin.binding == module.name
                        for module in origin.scope.children
                    )
                ):
                    target = _find_namespace_annotation_class(
                        hint, origin.scope, origin.binding, parts[1:],
                    )
                    if target is not None:
                        return target
                candidates.extend(
                    target for target in set(dependency.deps) | dependency.class_object_targets
                    if isinstance(target, ScopeRecord)
                    and (
                        target.kind == ScopeKind.MODULE and dependency.binding == target.name
                        or target.kind == ScopeKind.CLASS
                        and dependency.binding is not None
                        and any(
                            _is_annotation_source_class(target, module)
                            for module in dependency.scope.children
                            if module.name == dependency.binding.rpartition('.')[0]
                        )
                    )
                )
            continue
        if binding.declared_scope is not None:
            if binding.declared_scope.kind == ScopeKind.CLASS:
                candidates.append(binding.declared_scope)
            continue
        candidates.extend(binding.class_object_targets)
    if not bindings:
        return None
    candidates = list(dict.fromkeys(candidates))
    for index, part in enumerate(parts[1:], 1):
        if len(candidates) == 1:
            candidate = candidates[0]
            if (
                candidate.kind == ScopeKind.MODULE and candidate.parent is not None
                and not candidate.find_current_nodes(part)
            ):
                target = _find_namespace_annotation_class(
                    hint, candidate.parent, candidate.name, parts[index:],
                )
                if target is not None:
                    return target
        candidates = list(dict.fromkeys(
            member
            for candidate in candidates
            for binding in (
                candidate.find_current_nodes(part)
                if candidate.kind == ScopeKind.MODULE
                else _find_class_member_bindings(candidate, part) or []
            )
            if not binding.is_import or candidate.is_package_initializer
            for member in (
                ([binding.declared_scope] if binding.declared_scope is not None else [])
                + list(binding.class_object_targets)
                + [
                    target
                    for dependency in binding.deps
                    if binding.is_import
                    and isinstance(dependency, NodeRecord)
                    and dependency.scope.kind == ScopeKind.ROOT
                    for target in dependency.deps
                    if isinstance(target, ScopeRecord)
                    and target.kind == ScopeKind.MODULE
                ]
            )
            if (
                member.kind == ScopeKind.MODULE and candidate.is_package_initializer
                or _is_annotation_source_class(member, binding.scope)
                or candidate.kind == ScopeKind.CLASS
                and _is_annotation_source_class(candidate, hint.scope)
                and not binding.is_import and member in binding.class_object_targets
            )
        ))
    return (
        candidates[0]
        if len(candidates) == 1 and candidates[0].kind == ScopeKind.CLASS
        else None
    )


def _find_namespace_annotation_class(
    hint: AnnotationHint, root: ScopeRecord, namespace: str, parts: list[str],
) -> ScopeRecord | None:
    qualified = '.'.join((namespace, *parts))
    modules = [
        module for module in root.children
        if module.kind == ScopeKind.MODULE and module.name.startswith(f'{namespace}.')
        and qualified.startswith(f'{module.name}.')
    ]
    if not modules:
        return None
    module = min(modules, key=lambda item: len(item.name))
    target = _find_annotation_class(replace(
        hint, name=qualified[len(module.name) + 1:], scope=module,
        position=None, type_parameters=frozenset(),
    ))
    return target if target is not None and _is_annotation_source_class(target, module) else None


def _is_annotation_source_class(target: ScopeRecord, module: ScopeRecord) -> bool:
    if target.kind != ScopeKind.CLASS:
        return False
    while module.parent is not None and module.kind != ScopeKind.MODULE:
        module = module.parent
    owner = target.parent
    while owner is not None and owner.kind != ScopeKind.MODULE:
        owner = owner.parent
    return owner is module or module.is_package_initializer


def _is_name_deletion(node: NodeRecord) -> bool:
    return (
        node.kind == NodeKind.OPERATION
        and node.operation_type == OperationType.MUTATION
        and node.access == AccessMode.WRITE
    )


def _find_base_class_scopes(
    class_scope: ScopeRecord,
    base_read: Reference | None,
) -> list[ScopeRecord]:
    if base_read is None:
        return []
    owner = class_scope.parent
    assert owner is not None  # Source class declarations have an enclosing scope.
    declaration = class_scope.class_declaration

    candidates = []
    for binding in owner.find_nodes(base_read, before=declaration):
        if binding.declared_scope is not None:
            candidates.append(binding.declared_scope)
        candidates.extend(_find_class_object_targets(binding, declaration))
        if binding.is_import:
            for dependency in binding.deps:
                if not isinstance(dependency, NodeRecord):
                    continue
                if dependency.scope.kind == ScopeKind.ROOT:
                    candidates.extend(
                        target
                        for target in dependency.deps
                        if isinstance(target, ScopeRecord)
                    )
    class_candidates = []
    for candidate in candidates:
        if candidate.kind == ScopeKind.CLASS and candidate not in class_candidates:
            class_candidates.append(candidate)
    return class_candidates


def _find_class_member_scopes(
    class_scope: ScopeRecord,
    member_path: str,
    seen: set[int] | None = None,
) -> list[ScopeRecord]:
    members = []
    for binding, _ in _find_member_value_bindings(class_scope, member_path, seen):
        member = binding.declared_scope
        if member is not None and member not in members:
            members.append(member)
        for member in binding.callable_targets | _find_class_object_targets(binding):
            if member not in members:
                members.append(member)
    return members


def _find_super_member_scopes(
    node: NodeRecord,
    scope: ScopeRecord,
    member_name: str | None = None,
) -> list[ScopeRecord]:
    member_name = node.super_member if member_name is None else member_name
    if not node.is_super_call or member_name is None:
        return []
    return [
        member
        for base_scope in _find_super_base_scopes(scope)
        for member in _find_class_member_scopes(base_scope, member_name)
    ]


def _find_super_base_scopes(scope: ScopeRecord) -> list[ScopeRecord]:
    class_scope = scope.find_class_cell_scope('__class__')
    if (
        class_scope is None or class_scope.kind != ScopeKind.CLASS
        or len(class_scope.base_reads) != 1
    ):
        return []
    return _find_base_class_scopes(class_scope, class_scope.base_reads[0])


def _uses_builtin_super(node: NodeRecord, scope: ScopeRecord) -> bool:
    class_cell = scope.find_class_cell_scope('__class__')
    if not node.is_super_call or class_cell is None:
        return False
    if node.super_member is not None:
        return any(
            receiver.is_super_call
            and receiver.super_member is None
            and _uses_builtin_super(receiver, scope)
            for dependency in node.raw_receiver_deps
            for receiver in scope.find_nodes(dependency, before=node)
        )
    bindings = node.find_bindings('super')
    callee = node.raw_callee_deps[0]
    environment = callee.environment if isinstance(callee, Reference) else None
    return scope.find_nodes(
        '__class__', before=node, environment=environment,
    ) == [class_cell.class_declaration] and (
        all(_is_supported_annotation_binding(binding, {'builtins.super'}) for binding in bindings)
        if bindings else _is_supported_annotation_identity(
            scope, ast.Name(id='super'), node.scope_position, {'builtins.super'},
            environment=environment,
        )
    )


def _visible_types(
    scope: ScopeRecord,
    name: str | ast.expr,
    before: NodeRecord | None = None,
) -> set[AnnotationHint]:
    if isinstance(name, ast.expr):
        expression = name
    elif '[' in name:
        expression = ast.parse(name, mode='eval').body
    else:
        return _visible_binding_types(scope, name, before)
    if isinstance(expression, ast.Subscript):
        if isinstance(expression.slice, ast.Slice):
            return _resolve_subscript_types(
                _visible_types(scope, expression.value, before), is_slice=True,
            )
        if isinstance(expression.value, ast.Name):
            element_types = set()
            bindings = (
                before.find_bindings(expression.value.id)
                if before is not None and before.scope is scope
                else scope.find_nodes(expression.value.id, before=before)
            )
            for binding in bindings:
                element_types.update(
                    _resolve_subscript_types(binding.collect_type_hints(before))
                )
            return element_types
        return _resolve_subscript_types(
            _visible_types(scope, expression.value, before)
        )
    if isinstance(expression, ast.Name):
        return _visible_binding_types(scope, expression.id, before)
    if isinstance(name, ast.expr):
        return _visible_binding_types(scope, ast.unparse(expression), before)
    return _visible_binding_types(scope, name, before)


def _resolve_subscript_types(
    hints: set[AnnotationHint], *, is_slice: bool = False,
) -> set[AnnotationHint]:
    resolved_types = set()
    for hint in hints:
        expression = ast.parse(hint.name, mode='eval').body
        if not isinstance(expression, ast.Subscript):
            continue
        if not _is_supported_annotation_identity(
            hint.scope, expression.value, hint.position, _SUPPORTED_CONTAINER_IMPORTS,
            hint.type_parameters, environment=hint.environment,
        ):
            continue
        if is_slice:
            resolved_types.add(hint)
            continue
        arguments = (
            expression.slice.elts
            if isinstance(expression.slice, ast.Tuple)
            else [expression.slice]
        )
        resolved_types.update(
            replace(hint, name=ast.unparse(argument))
            for argument in arguments
            if not isinstance(argument, (ast.Starred, ast.Slice))
            and (not isinstance(argument, ast.Constant) or argument.value is not Ellipsis)
        )
    return resolved_types


def _has_direct_member_write(
    scope: ScopeRecord,
    receiver_bindings: list[NodeRecord],
    attribute_expression: ast.expr | str,
    before: NodeRecord | None,
    *, position: int | None = None,
) -> bool:
    expression_key = _attribute_expression_key(attribute_expression)
    if expression_key is None:
        return False
    if before is not None:
        position = before.scope_position
    return any(
        binding is receiver or (
            receiver.attribute_expression is not None
            and binding in receiver.find_bindings(
                _attribute_receiver_path(write.attribute_expression)[0]
            )
        )
        for write in scope.nodes
        if (
            write.kind == NodeKind.REFERENCE
            and write.access == AccessMode.WRITE
            and write.attribute_expression is not None
            and (write_key := _attribute_expression_key(write.attribute_expression))
            is not None
            and write_key[0] == expression_key[0]
            and expression_key[1][:len(write_key[1])] == write_key[1]
            and (position is None or cast(int, write.scope_position) < position)
            and (before is None or not any(
                (condition, not arm) in before.branch_context
                for condition, arm in write.branch_context
            ))
        )
        for occurrence in write.inputs[:1]
        for receiver in scope.find_nodes(occurrence.source or occurrence.name, before=write)
        for binding in receiver_bindings
    )


def _attribute_expression_key(
    expression: ast.expr | str,
) -> tuple[str, tuple[str, ...]] | None:
    if isinstance(expression, str):
        expression = ast.parse(expression, mode='eval').body
    if not isinstance(expression, ast.Attribute):
        return None
    attributes = []
    while isinstance(expression, ast.Attribute):
        attributes.append(expression.attr)
        expression = expression.value
    return ast.dump(expression, include_attributes=False), tuple(reversed(attributes))


def _attribute_receiver_path(expression: ast.expr) -> tuple[str, str]:
    members = []
    while isinstance(expression, ast.Attribute):
        members.append(expression.attr)
        expression = expression.value
    return ast.unparse(expression), '.'.join(reversed(members))


def _find_call_member_path(node: NodeRecord, name: str) -> tuple[str, str]:
    for reference in node.raw_callee_deps:
        for callee in node.scope.find_nodes(reference, before=node):
            if callee.attribute_expression is not None:
                return _attribute_receiver_path(callee.attribute_expression)
    expression = ast.parse(name, mode='eval').body
    if isinstance(expression, ast.Attribute):
        return _attribute_receiver_path(expression)
    return name, ''


def _is_supported_annotation_identity(
    scope: ScopeRecord,
    expression: ast.expr,
    position: int | None,
    supported_imports: set[str],
    type_parameters: frozenset[str] = frozenset(),
    environment: BindingEnvironment | None = None,
    before: NodeRecord | None = None,
) -> bool:
    if isinstance(expression, ast.Name):
        if expression.id in type_parameters:
            return False
        bindings = [
            binding for binding in scope.find_nodes(
                expression.id, position=position, environment=environment,
            )
            if not binding.is_deletion
        ]
        if not bindings:
            return (
                f'builtins.{expression.id}' in supported_imports
                and not _has_source_binding(
                    scope, Reference(
                        expression.id, scope, position, environment=environment,
                    ), None
                )
            )
        return all(
            _is_supported_annotation_binding(binding, supported_imports)
            for binding in bindings
        )

    attribute_expression = expression
    attributes: list[str] = []
    while isinstance(expression, ast.Attribute):
        attributes.insert(0, expression.attr)
        expression = expression.value
    if not isinstance(expression, ast.Name) or expression.id in type_parameters:
        return False
    bindings = scope.find_nodes(
        expression.id, position=position, environment=environment,
    )
    suffix = '.' + '.'.join(attributes)
    return bool(bindings) and not _has_direct_member_write(
        scope, bindings, attribute_expression, before, position=position,
    ) and all(
        _is_supported_annotation_binding(binding, supported_imports, suffix)
        for binding in bindings
    )


def _is_supported_annotation_binding(
    binding: NodeRecord, supported_imports: set[str], suffix: str = '',
) -> bool:
    binding = _find_alias_target(binding) or binding
    if binding.scope.kind == ScopeKind.BUILTINS:
        return f'builtins.{binding.binding}{suffix}' in supported_imports
    return binding.is_import and any(
        isinstance(dependency, NodeRecord)
        and dependency.scope.kind == ScopeKind.ROOT
        and f'{dependency.binding}{suffix}' in supported_imports
        and not any(
            module.kind == ScopeKind.MODULE and (
                f'{dependency.binding}{suffix}' == module.name
                or f'{dependency.binding}{suffix}'.startswith(f'{module.name}.')
                or module.name.startswith(f'{dependency.binding}{suffix}.')
            )
            for module in dependency.scope.children
        )
        for dependency in binding.deps
    )


def _visible_binding_types(
    scope: ScopeRecord,
    name: str,
    before: NodeRecord | None = None,
) -> set[AnnotationHint]:
    bindings = (
        before.find_bindings(name)
        if before is not None and before.scope is scope
        else scope.find_nodes(name, before=before)
    )
    return {
        type_name
        for binding in bindings
        for type_name in binding.collect_type_hints(before)
    }


def _infer_binding_targets(node: NodeRecord) -> None:
    if node.kind == NodeKind.SUBSCRIPT and node.subscript_expression is not None:
        node.inferred_types.update(
            _visible_types(node.scope, node.subscript_expression, node)
        )
    if node.declared_scope is not None or (
        node.scope.kind == ScopeKind.ROOT and node.class_object_targets
    ):
        # Constructor dependencies do not change a canonical target's class identity.
        return
    dependencies: Iterable[NodeRecord | ScopeRecord] = node.deps
    is_value_alias = (
        node.is_import or node.scope.kind == ScopeKind.ROOT
        or node.binding is not None and len(node.collect_value_inputs()) == 1
    )
    is_value_selection = node.binding is None
    if is_value_selection:
        if not node.value_sources:
            return
        dependencies = [
            dependency
            for source in node.value_sources
            for dependency in node.scope.find_nodes(source, before=node)
        ]
    for dependency in dependencies:
        if isinstance(dependency, ScopeRecord) and dependency.kind == ScopeKind.CLASS:
            node.class_object_targets.add(dependency)
        if not isinstance(dependency, NodeRecord):
            continue
        if dependency.declared_scope is not None and dependency.declared_scope.kind == ScopeKind.CLASS:
            node.class_object_targets.add(dependency.declared_scope)
        if dependency.declared_scope is not None and dependency.declared_scope.kind == ScopeKind.FUNCTION:
            node.callable_targets.add(dependency.declared_scope)
        if (
            (is_value_selection or is_value_alias)
            and (
                dependency.kind.is_value
                or dependency.kind in (
                    NodeKind.REFERENCE,
                    NodeKind.SUBSCRIPT,
                    NodeKind.CALL,
                )
                or dependency.value_sources
            )
        ):
            node.inferred_types.update(dependency.collect_type_hints(
                None if node.scope.kind == ScopeKind.ROOT else node
            ))
        node.class_object_targets.update(_find_class_object_targets(dependency, node))
        node.callable_targets.update(dependency.callable_targets)
        if dependency.kind == NodeKind.CALL:
            node.inferred_classes.update(dependency.resolved_class_targets)
        else:
            node.inferred_classes.update(dependency.inferred_classes)
        if dependency.scope.kind == ScopeKind.ROOT:
            node.class_object_targets.update(
                target
                for target in dependency.deps
                if isinstance(target, ScopeRecord) and target.kind == ScopeKind.CLASS
            )


def _find_class_member_bindings(
    class_scope: ScopeRecord,
    member_name: str,
    seen: set[int] | None = None,
) -> list[NodeRecord] | None:
    """Find member candidates; None means an unresolved base blocked lookup."""
    seen = set() if seen is None else seen
    if id(class_scope) in seen:
        return None
    seen.add(id(class_scope))
    bindings = class_scope.find_member_nodes(member_name)
    members = [binding for binding in bindings if not _is_name_deletion(binding)]
    needs_inherited = any(_is_name_deletion(binding) for binding in bindings) or not any(
        not class_scope.is_binding_conditional(binding)
        and not _is_name_deletion(binding)
        for binding in bindings
    )
    if needs_inherited:
        for base_read in class_scope.base_reads:
            base_scopes = _find_base_class_scopes(class_scope, base_read)
            if not base_scopes:
                return members or None
            inherited: list[NodeRecord] = []
            blocked = False
            for base_scope in base_scopes:
                base_members = _find_class_member_bindings(base_scope, member_name, set(seen))
                if base_members is None:
                    blocked = True
                    continue
                inherited.extend(
                    binding
                    for binding in base_members
                    if binding not in inherited
                )
            members.extend(binding for binding in inherited if binding not in members)
            if inherited:
                break
            if blocked:
                return members or None
    return members


def _find_member_value_bindings(
    class_scope: ScopeRecord,
    member_path: str,
    seen: set[int] | None = None,
) -> list[tuple[NodeRecord, ScopeRecord]]:
    """Find endpoint bindings together with their actual receiver scopes."""
    seen = set() if seen is None else seen
    owners = [class_scope]
    bindings: list[tuple[NodeRecord, ScopeRecord]] = []
    for part in member_path.split('.'):
        bindings = []
        for owner in owners:
            if owner.kind not in (ScopeKind.CLASS, ScopeKind.MODULE):
                continue
            if owner.kind == ScopeKind.CLASS:
                candidates = _find_class_member_bindings(owner, part, set(seen)) or []
            else:
                candidates = owner.find_current_nodes(part)
            bindings.extend(
                (candidate, owner) for candidate in candidates
                if (candidate, owner) not in bindings
            )
        owners = []
        for binding, _ in bindings:
            if binding.declared_scope is not None and binding.declared_scope not in owners:
                owners.append(binding.declared_scope)
            for target in (
                binding.callable_targets | _find_class_object_targets(binding) | binding.inferred_classes
            ):
                if target not in owners:
                    owners.append(target)
    return bindings


def _resolve_member_value(node: NodeRecord, scope: ScopeRecord) -> None:
    if (
        node.kind != NodeKind.REFERENCE
        or node.access != AccessMode.READ
        or node.attribute_expression is None
    ):
        return
    is_callee = any(
        candidate.kind == NodeKind.CALL
        and node.reference in candidate.raw_callee_deps
        for candidate in scope.nodes
    )
    receiver, member_path = _attribute_receiver_path(node.attribute_expression)
    if receiver == 'super()':
        super_call = next(
            (
                dependency
                for dependency in node.deps
                if isinstance(dependency, NodeRecord)
                and dependency.kind == NodeKind.CALL
                and dependency.is_super_call
            ),
            None,
        )
        if super_call is not None and _uses_builtin_super(super_call, scope):
            for base_scope in _find_super_base_scopes(scope):
                for binding, _ in _find_member_value_bindings(base_scope, member_path):
                    if not is_callee or not _is_empty_scope_binding(binding):
                        node.add_dependency(binding, access=AccessMode.READ)
            for member_scope in _find_super_member_scopes(
                super_call, scope, member_path
            ):
                node.callable_targets.add(member_scope)
        return
    predicate_refs = {predicate.reference for predicate in node.predicates}
    receiver_dependencies = [
        dependency
        for occurrence in node.inputs
        if not occurrence.is_structural
        and (dependency := occurrence.source or occurrence.name) not in predicate_refs
    ]
    if len(receiver_dependencies) != 1:
        return
    receivers = scope.find_nodes(receiver_dependencies[0], before=node)
    root_bindings = node.find_bindings(receiver)
    if (
        node.attribute_expression is not None
        and _has_direct_member_write(
            scope, root_bindings + receivers, node.attribute_expression, node
        )
    ):
        return
    class_targets = {
        target
        for binding in receivers
        for target in (
            _find_class_object_targets(binding, node)
            | _find_instance_class_targets(binding, node)
        )
    }
    if class_targets:
        receiver = ast.unparse(node.attribute_expression.value)
        member_path = node.attribute_expression.attr
    else:
        class_targets.update(
            target
            for binding in root_bindings
            for target in _find_class_object_targets(binding, node) | binding.inferred_classes
        )
    class_targets.update(
        class_scope
        for type_name in _visible_types(scope, receiver, node)
        if (
            class_scope := _find_annotation_class(type_name)
        ) is not None
        and class_scope.kind == ScopeKind.CLASS
    )
    for class_scope in sorted(
        class_targets,
        key=lambda target: (target.span or (0, 0, 0, 0), target.name),
    ):
        for binding, member_owner in _find_member_value_bindings(class_scope, member_path):
            # Calls receive outputs separately; retain declaration inputs
            # such as defaults and decorators on the member value.
            if is_callee and _is_empty_scope_binding(binding):
                continue
            node.add_dependency(binding, access=AccessMode.READ)
            _propagate_member_targets(node, binding, before=node)
            if (
                binding.declared_scope is not None
                and _uses_builtin_decorator(binding, 'classmethod')
            ):
                node.add_dependency(member_owner, access=AccessMode.READ)


def _propagate_member_targets(
    node: NodeRecord, binding: NodeRecord, before: NodeRecord | None = None,
) -> None:
    """Preserve a member's known targets and annotation origins on its read."""
    if binding.declared_scope is not None:
        if binding.declared_scope.kind == ScopeKind.FUNCTION:
            node.callable_targets.add(binding.declared_scope)
        elif binding.declared_scope.kind == ScopeKind.CLASS:
            node.class_object_targets.add(binding.declared_scope)
    node.callable_targets.update(binding.callable_targets)
    node.class_object_targets.update(_find_class_object_targets(binding, before))
    node.inferred_classes.update(binding.inferred_classes)
    node.inferred_types.update(binding.collect_type_hints(before))


def _resolve_node(node: NodeRecord, scope: ScopeRecord) -> None:
    _resolve_member_value(node, scope)

    for name in node.raw_calls:
        super_scopes = (
            _find_super_member_scopes(node, scope)
            if _uses_builtin_super(node, scope)
            else []
        )
        if super_scopes:
            for super_scope in super_scopes:
                _add_call_targets(node, super_scope)
            continue
        bindings = (
            [
                dependency
                for callee_dependency in node.raw_callee_deps
                for dependency in scope.find_nodes(callee_dependency, before=node)
            ]
            if node.is_dynamic_call or node.raw_callee_deps
            else scope.find_nodes(name, before=node)
        )
        has_imported_target = bool(node.resolved_import_targets) or any(
            isinstance(dependency, NodeRecord)
            and dependency.scope.kind == ScopeKind.ROOT
            for dependency in node.deps
        )
        class_cell = scope.find_class_cell_scope(name)
        if not bindings and class_cell is not None:
            node.resolved_class_targets.add(class_cell)
            _add_call_targets(node, class_cell)
            _add_constructor_targets(node, class_cell)
            continue
        if bindings and (
            node.is_dynamic_call
            or any(binding.attribute_expression is None for binding in bindings)
        ):
            for binding in bindings:
                called_scope = binding.declared_scope
                if called_scope is not None:
                    if called_scope.kind == ScopeKind.CLASS:
                        node.resolved_class_targets.add(called_scope)
                    _add_call_targets(node, called_scope)
                    _add_constructor_targets(node, called_scope)
                else:
                    for callable_scope in sorted(
                        binding.callable_targets,
                        key=lambda target: (target.span or (0, 0, 0, 0), target.name),
                    ):
                        _add_call_targets(node, callable_scope)
                    # Imported classes supply receiver types through their
                    # canonical targets; they do not add direct callee edges.
                    if binding.is_import:
                        continue
                    for class_scope in sorted(
                        _find_class_object_targets(binding, node),
                        key=lambda target: (target.span or (0, 0, 0, 0), target.name),
                    ):
                        node.resolved_class_targets.add(class_scope)
                        _add_call_targets(node, class_scope)
                        _add_constructor_targets(node, class_scope)
            continue

        if has_imported_target:
            continue
        receiver, member_path = _find_call_member_path(node, name)
        if member_path:
            receiver_bindings = node.find_bindings(receiver)
            member_scopes = []
            if not _has_direct_member_write(
                scope, receiver_bindings, name, node
            ):
                for binding in receiver_bindings:
                    for class_scope in sorted(
                        _find_class_object_targets(binding, node) | binding.inferred_classes,
                        key=lambda target: (target.span or (0, 0, 0, 0), target.name),
                    ):
                        for member_scope in _find_class_member_scopes(class_scope, member_path):
                            if member_scope not in member_scopes:
                                member_scopes.append(member_scope)
                for source in node.raw_receiver_deps:
                    for binding in scope.find_nodes(source, before=node):
                        class_targets = _find_instance_class_targets(binding, node)
                        if binding.kind in (NodeKind.SUBSCRIPT, NodeKind.REFERENCE):
                            class_targets.update(_find_class_object_targets(binding, node))
                        for class_scope in sorted(
                            class_targets,
                            key=lambda target: (target.span or (0, 0, 0, 0), target.name),
                        ):
                            # This receiver already represents the preceding path.
                            for member_scope in _find_class_member_scopes(
                                class_scope, member_path.rsplit('.', 1)[-1]
                            ):
                                if member_scope not in member_scopes:
                                    member_scopes.append(member_scope)
            if member_scopes:
                for member_scope in member_scopes:
                    if member_scope.kind == ScopeKind.CLASS:
                        node.resolved_class_targets.add(member_scope)
                    _add_call_targets(node, member_scope)
                    _add_constructor_targets(node, member_scope)
                continue
            if receiver_bindings:
                continue
        local_name = name.partition('.')[0]
        if (
            scope.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION)
            and local_name in scope.defines
            and not node.find_bindings(local_name)
        ):
            continue

    _infer_binding_targets(node)


def resolve(scopes: list[ScopeRecord]) -> None:
    _resolve_builtin_dependencies(scopes)
    _seed_method_receivers(scopes)
    resolve_dependencies(scopes)


def resolve_dependencies(scopes: list[ScopeRecord]) -> None:
    """Connect lexical inputs, then propagate known dependency and target facts."""
    expressions: dict[str | Reference, NodeRecord] = {
        node.reference: node
        for scope in scopes for node in scope.nodes
        if node.reference is not None
    }
    # Member-write visibility must see all lexical inputs before any call or
    # member lookup infers targets from those bindings.
    for scope in scopes:
        for node in scope.nodes:
            for occurrence in node.inputs:
                expression = expressions.get(occurrence.name)
                dependencies: Sequence[NodeRecord | ScopeRecord] = (
                    [expression] if expression is not None and expression.scope is not scope
                    else scope.find_nodes(occurrence.source or occurrence.name, before=node)
                )
                if not dependencies:
                    class_cell = scope.find_class_cell_scope(occurrence.source or occurrence.name)
                    if class_cell is not None:
                        dependencies = [class_cell]
                for dependency in dependencies:
                    node.add_dependency(dependency, occurrence)
    while _propagate_dependencies(scopes):
        pass


def _propagate_dependencies(scopes: list[ScopeRecord]) -> bool:
    """Apply one target-propagation pass and report whether facts grew."""
    changed = False
    for scope in scopes:
        if scope.kind == ScopeKind.BUILTINS:
            continue
        for node in scope.nodes:
            before = _collect_resolution_counts(node)
            _resolve_node(node, scope)
            if _collect_resolution_counts(node) != before:
                changed = True
    return changed


def _collect_resolution_counts(node: NodeRecord) -> tuple[int, ...]:
    # Target facts participate even before their dependency edges are emitted.
    return (
        len(node.deps),
        len(node.inferred_types),
        len(node.inferred_classes),
        len(node.class_object_targets),
        len(node.callable_targets),
        len(node.resolved_call_targets),
        len(node.resolved_class_targets),
        len(node.resolved_import_targets),
    )


def resolve_read_occurrences(scopes: list[ScopeRecord]) -> None:
    """Complete IR read endpoints before lowering, including unresolved reads.

    Distinct occurrence identities preserve repeated reads. Alternative binding
    versions remain targets of one occurrence. Missing endpoints are registered
    as ordinary unresolved IR nodes through the same factory as other resolution.
    """
    referenced_nodes: dict[str | Reference, NodeRecord] = {
        node.reference: node
        for scope in scopes
        for node in scope.nodes
        if node.reference is not None
    }
    for scope in scopes:
        unresolved_by_name: dict[str | Reference, NodeRecord] = {
            node.binding: node
            for node in scope.nodes
            if node.is_unresolved and node.binding is not None
        }
        for node in list(scope.nodes):
            node.read_targets = node.collect_read_targets()
            dependencies = set(node.deps)
            for occurrence, targets in node.read_targets.items():
                if not targets:
                    dependency: NodeRecord | ScopeRecord | None = referenced_nodes.get(occurrence.name)
                    if dependency is None:
                        dependency = _unresolved_node(
                            scope, unresolved_by_name, occurrence.name,
                        )
                    targets = node.read_targets[occurrence] = (dependency,)
                dependency = targets[0]
                if (
                    isinstance(dependency, NodeRecord)
                    and (
                        dependency.is_unresolved
                        or dependency.kind is NodeKind.VARIABLE
                    )
                    and dependency not in dependencies
                ):
                    node.add_dependency(dependency, occurrence)


def _find_instance_class_targets(
    binding: NodeRecord, before: NodeRecord,
) -> set[ScopeRecord]:
    """Collect classes from inferred instances, constructor results, and annotations."""
    targets = set(
        binding.resolved_class_targets
        if binding.kind == NodeKind.CALL else binding.inferred_classes
    )
    for hint in binding.collect_type_hints(before):
        class_scope = _find_annotation_class(hint)
        if class_scope is not None:
            targets.add(class_scope)
    return targets


def _find_class_object_targets(
    binding: NodeRecord, before: NodeRecord | None = None
) -> set[ScopeRecord]:
    targets = set(binding.class_object_targets)
    for hint in binding.collect_type_hints(before):
        expression = _unwrap_class_object_annotation(
            hint, ast.parse(hint.name, mode='eval').body,
        )
        if expression is None:
            continue
        class_scope = _find_annotation_class(replace(hint, name=ast.unparse(expression)))
        if class_scope is not None and class_scope.kind == ScopeKind.CLASS:
            targets.add(class_scope)
    return targets


def _unwrap_class_object_annotation(
    hint: AnnotationHint, expression: ast.expr,
) -> ast.expr | None:
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.slice, (ast.Name, ast.Attribute, ast.Constant))
        and _is_supported_annotation_identity(
            hint.scope, expression.value, hint.position, {'builtins.type'},
            hint.type_parameters, environment=hint.environment,
        )
    ):
        return expression.slice
    return None


def _seed_method_receivers(scopes: list[ScopeRecord]) -> None:
    receivers: dict[NodeRecord, bool] = {}
    for scope in scopes:
        owner = scope.parent
        if (
            scope.kind != ScopeKind.FUNCTION
            or owner is None
            or owner.kind != ScopeKind.CLASS
        ):
            continue
        declaration = next(
            (node for node in owner.nodes if node.declared_scope is scope), None
        )
        if declaration is None or declaration.is_global_write or declaration.is_nonlocal_write:
            continue
        if declaration.binding is None and not any(
            member.binding is not None
            and member.declared_scope is None
            and not member.is_global_write
            and not member.is_nonlocal_write
            and [occurrence.name for occurrence in member.collect_value_inputs()]
            == [declaration.reference]
            for member in owner.nodes
        ):
            continue
        is_classmethod = _uses_builtin_decorator(declaration, 'classmethod')
        if _uses_builtin_decorator(declaration, 'staticmethod'):
            continue
        first_parameter = next(
            (
                node
                for node in scope.nodes
                if node.is_first_positional_parameter
            ),
            None,
        )
        if first_parameter is not None:
            receivers[first_parameter] = is_classmethod
            if is_classmethod:
                first_parameter.class_object_targets.add(owner)
            else:
                first_parameter.inferred_classes.add(owner)

    for scope in scopes:
        for node in scope.nodes:
            expression = node.attribute_expression
            if expression is None:
                continue
            node.is_instance_attribute = False
            node.is_class_attribute = False
            root = expression.value
            while isinstance(root, ast.Attribute):
                root = root.value
            if not isinstance(root, ast.Name):
                continue
            for binding in node.find_bindings(root.id):
                if binding in receivers:
                    if receivers[binding]:
                        node.is_class_attribute = True
                    else:
                        node.is_instance_attribute = True


def _uses_builtin_decorator(declaration: NodeRecord, name: str) -> bool:
    for read in declaration.decorator_reads:
        scope = read.read_scope or declaration.scope
        expression = ast.parse(read.description, mode='eval').body
        if _is_supported_annotation_identity(
            scope, expression, read.read_position, {'builtins.classmethod'},
            environment=read.environment,
            before=declaration,
        ):
            return name == 'classmethod'
        if _is_supported_annotation_identity(
            scope, expression, read.read_position, {'builtins.staticmethod'},
            environment=read.environment,
            before=declaration,
        ):
            return name == 'staticmethod'
    return False


def resolve_external_imports(
    scopes: list[ScopeRecord],
    shadowed_module_members: set[tuple[NodeRecord, str]] | None = None,
) -> None:
    """Connect imported callees to shared targets after internal resolution.

    Import bindings already depend on root targets. Qualified calls add an edge
    to the member target, without interpreting argument dependencies as callees.
    External modules are never imported or inspected.
    """
    root = next(scope for scope in scopes if scope.kind == ScopeKind.ROOT)
    for scope in scopes:
        if scope.kind in (ScopeKind.ROOT, ScopeKind.BUILTINS):
            continue
        for node in scope.nodes:
            if not node.raw_calls:
                continue
            for name in node.raw_calls:
                if node.is_dynamic_call:
                    continue
                binding, member = _find_call_member_path(node, name)
                receiver_bindings = node.find_bindings(binding)
                if member and _has_direct_member_write(scope, receiver_bindings, name, node):
                    continue
                for receiver_binding in receiver_bindings:
                    if shadowed_module_members and (
                        receiver_binding, member
                    ) in shadowed_module_members:
                        continue
                    if member and _has_resolved_call(node, name) and (
                        receiver_binding.inferred_classes or receiver_binding.collect_type_hints(node)
                    ):
                        continue
                    imported = _find_alias_target(receiver_binding)
                    if imported is None or not imported.is_import:
                        continue
                    for dependency in imported.deps:
                        if (
                            not isinstance(dependency, NodeRecord)
                            or dependency.scope is not root
                        ):
                            continue
                        if not member:
                            continue
                        forwarded_name = _find_forwarded_call_name(node, member.rsplit(".", 1)[-1])
                        if forwarded_name is not None:
                            canonical = forwarded_name
                        else:
                            origin = _find_import_origin(dependency)
                            if not origin.deps:
                                dependency = origin
                            canonical = f'{dependency.binding}.{member}'
                        targets = root.bindings.get(canonical)
                        if targets is None:
                            target = NodeRecord(
                                canonical, root, kind=NodeKind.IMPORT_TARGET,
                                binding=canonical,
                            )
                            root.nodes.append(target)
                            targets = root.bindings[canonical] = [target]
                        node.resolved_import_targets.add(targets[0])
            imported_call_targets = _collect_import_call_targets(node)
            member_dependencies = {
                dependency
                for reference in node.raw_callee_deps
                for member in scope.find_nodes(reference, before=node)
                if member.kind == NodeKind.REFERENCE
                for dependency in member.collect_forwarded_dependencies()
            }
            for target in node.resolved_import_targets:
                if target.callable_targets and target.deps and all(
                    isinstance(dependency, NodeRecord)
                    and dependency.declared_scope is not None
                    and dependency.declared_scope.kind == ScopeKind.FUNCTION
                    for dependency in target.deps
                ) and (
                    target in member_dependencies or all(
                        dependency in member_dependencies for dependency in target.deps
                    )
                ):
                    continue
                node.add_dependency(target, access=AccessMode.READ)
            represented_dependencies = {
                dependency
                for target in imported_call_targets
                for dependency in target.collect_forwarded_dependencies()
                if dependency not in imported_call_targets
            }
            for dependency in represented_dependencies:
                inputs = node.deps.get(dependency)
                if inputs is not None:
                    # The import target carries inferred relationships; retain source inputs.
                    for occurrence in tuple(inputs):
                        if occurrence not in node.inputs:
                            del inputs[occurrence]
                    if not inputs:
                        del node.deps[dependency]
    used = {id(dep) for scope in scopes for node in scope.nodes for dep in node.deps}
    root.nodes[:] = [node for node in root.nodes if id(node) in used]
    root.bindings = {cast(str, node.binding): [node] for node in root.nodes}
    _add_unresolved_nodes(scopes)


def _collect_import_call_targets(node: NodeRecord) -> set[NodeRecord]:
    targets = set(node.resolved_import_targets)
    for dependency, occurrences in node.deps.items():
        if not isinstance(dependency, NodeRecord) or not any(
            occurrence is not None and occurrence.is_callee for occurrence in occurrences
        ):
            continue
        imported = _find_alias_target(dependency)
        if imported is not None and imported.is_import:
            targets.update(
                target for target in imported.deps
                if isinstance(target, NodeRecord) and target.scope.kind == ScopeKind.ROOT
            )
    return targets


def _find_forwarded_call_name(node: NodeRecord, member: str) -> str | None:
    pending = [
        (receiver, member)
        for source in node.raw_receiver_deps
        for receiver in node.scope.find_nodes(source, before=node)
    ]
    names: set[str] = set()
    while pending:
        receiver, suffix = pending.pop()
        if receiver.kind != NodeKind.REFERENCE or receiver.attribute_expression is None:
            continue
        targets = {
            forwarded
            for dependency in receiver.deps
            if isinstance(dependency, NodeRecord) and dependency.scope.kind == ScopeKind.ROOT
            and (forwarded := _find_import_origin(dependency)) is not dependency
            and not forwarded.deps
        }
        if targets:
            names.update(f'{target.binding}.{suffix}' for target in targets)
            continue
        pending.extend(
            (dependency, f'{receiver.attribute_expression.attr}.{suffix}')
            for occurrence in receiver.collect_value_inputs()
            for dependency in receiver.scope.find_nodes(
                occurrence.source or occurrence.name, before=receiver,
            )
        )
    return next(iter(names)) if len(names) == 1 else None


def _find_import_origin(target: NodeRecord) -> NodeRecord:
    """Follow linear re-exports to their original imported value."""
    original = target
    seen = set()
    while target not in seen:
        seen.add(target)
        if not target.deps:
            return target
        if target.class_object_targets or len(target.deps) != 1:
            return target
        binding = next(iter(target.deps))
        if not isinstance(binding, NodeRecord):
            return target
        imported = _find_alias_target(binding)
        if imported is None or not imported.is_import or len(imported.deps) != 1:
            return target
        forwarded = next(iter(imported.deps))
        if not isinstance(forwarded, NodeRecord) or forwarded.scope.kind != ScopeKind.ROOT:
            return target
        target = forwarded
    return original


def _find_alias_target(binding: NodeRecord) -> NodeRecord | None:
    """Follow one linear name-alias chain using captured lexical lookup points."""
    seen = set()
    while binding not in seen:
        if (
            binding.is_import or binding.scope.kind == ScopeKind.BUILTINS
            or binding.declared_scope is not None
        ):
            return binding
        if (
            not binding.kind.is_value or binding.binding is None
        ):
            return None
        inputs = binding.collect_value_inputs()
        if len(inputs) != 1:
            return None
        occurrence = inputs[0]
        targets = [
            target
            for target in binding.scope.find_nodes(
                occurrence.source or occurrence.name, before=binding
            )
            if not target.is_deletion
        ]
        if not targets:
            targets = [
                target for target, inputs in binding.deps.items()
                if isinstance(target, NodeRecord)
                and target.scope.kind == ScopeKind.BUILTINS
                and occurrence in inputs
            ]
        if len(targets) != 1:
            return None
        seen.add(binding)
        binding = targets[0]
    return None


def _add_unresolved_nodes(scopes: list[ScopeRecord]) -> None:
    unresolved_by_scope: dict[ScopeRecord, dict[str | Reference, NodeRecord]] = {
        scope: {
            node.binding: node
            for node in scope.nodes
            if node.is_unresolved and node.binding is not None
        }
        for scope in scopes
    }
    for scope in scopes:
        if scope.kind in (ScopeKind.ROOT, ScopeKind.BUILTINS):
            continue
        nodes = list(scope.nodes)
        for node in nodes:
            if node.is_unresolved:
                continue
            for occurrence in node.inputs:
                name = occurrence.name
                if isinstance(name, Reference):
                    continue
                has_read = (
                    any(
                        occurrence in inputs
                        for dependency, inputs in node.deps.items()
                        if not isinstance(dependency, NodeRecord) or not dependency.is_unresolved
                    )
                    if occurrence.source is not None
                    else _has_resolved_read(node, name)
                )
                if has_read or (
                    name in node.raw_calls and _has_resolved_call(node, name)
                ):
                    continue
                read_scope = (
                    occurrence.source.read_scope
                    if occurrence.source is not None
                    and occurrence.source.read_scope is not None
                    else scope
                )
                placeholder = _unresolved_node(
                    read_scope, unresolved_by_scope[read_scope], name
                )
                node.add_dependency(placeholder, occurrence)


def _unresolved_node(
    scope: ScopeRecord,
    unresolved_by_name: dict[str | Reference, NodeRecord],
    name: str | Reference,
) -> NodeRecord:
    if name in unresolved_by_name:
        return unresolved_by_name[name]
    label = name.description if isinstance(name, Reference) else name
    node = NodeRecord(
        name=label,
        scope=scope,
        kind=NodeKind.UNRESOLVED_VALUE,
        binding=label,
        is_unresolved=True,
        display_name=label,
    )
    scope.nodes.append(node)
    unresolved_by_name[name] = node
    return node


def _has_resolved_read(node: NodeRecord, name: str | Reference) -> bool:
    class_scope = node.scope.find_class_cell_scope(name)
    return any(
        (
            isinstance(dependency, NodeRecord)
            and not dependency.is_unresolved
            and (
                dependency.binding == name
                or dependency.reference is name
                or (
                    class_scope is not None
                    and dependency.declared_scope is class_scope
                )
            )
        )
        or (
            isinstance(dependency, ScopeRecord)
            and (
                dependency.symbol == name
                or (class_scope is not None and dependency is class_scope)
            )
        )
        for dependency in node.deps
    )


def _has_resolved_call(node: NodeRecord, name: str) -> bool:
    if node.resolved_call_targets or node.resolved_class_targets or node.resolved_import_targets:
        return True
    binding = name.partition('.')[0]
    member = name.rpartition('.')[2]
    callee = next((occurrence.name for occurrence in node.inputs if occurrence.is_callee), None)
    for dependency, inputs in node.deps.items():
        if inputs and all(
            occurrence is not None and not occurrence.is_callee
            for occurrence in inputs
        ):
            continue
        if isinstance(dependency, ScopeRecord):
            if dependency.symbol == member or dependency.symbol is callee:
                return True
            continue
        if dependency.is_unresolved:
            continue
        if (
            dependency.scope.kind == ScopeKind.ROOT
            and dependency.binding is not None
            and dependency.binding.rpartition('.')[2] == member
        ):
            return True
        if dependency.binding == name and any(
            occurrence is not None and occurrence.is_callee for occurrence in inputs
        ):
            target = _find_alias_target(dependency)
            if target is not None and target.scope.kind == ScopeKind.BUILTINS:
                return True
        if dependency.binding == binding and dependency.callable_targets:
            return True
        if (
            dependency.declared_scope is not None
            and isinstance(callee, str)
            and dependency.binding == callee
        ):
            return True
        if dependency.output_type is not None and (
            dependency.scope.symbol == member
            or dependency.scope.symbol is callee
        ):
            return True
        if (
            dependency.is_import
            and dependency.binding == binding
            and any(
                isinstance(target, NodeRecord)
                and target.scope.kind == ScopeKind.ROOT
                for target in dependency.deps
            )
        ):
            return True
    return False


def _resolve_builtin_dependencies(scopes: list[ScopeRecord]) -> None:
    builtin_scope = next(
        (scope for scope in scopes if scope.kind == ScopeKind.BUILTINS),
        ScopeRecord(name='builtins', kind=ScopeKind.BUILTINS),
    )
    builtin_names = vars(builtins).keys() - {
        '__name__', '__doc__', '__package__', '__loader__', '__spec__',
    }
    imported_targets = {
        target for scope in scopes for node in scope.nodes
        for target in _collect_import_call_targets(node)
    }
    imported_targets.update(
        dependency for target in tuple(imported_targets)
        for dependency in target.collect_forwarded_dependencies()
        if isinstance(dependency, NodeRecord)
    )
    imported_calls = {
        target for target in imported_targets
        if target.binding is not None and target.binding.startswith('builtins.')
        and target.binding.removeprefix('builtins.') in builtin_names
        and not any(
            scope.kind == ScopeKind.MODULE and (
                target.binding == scope.name
                or target.binding.startswith(f'{scope.name}.')
                or scope.name.startswith(f'{target.binding}.')
            )
            for scope in scopes
        )
    }
    for scope in list(scopes):
        if scope.kind == ScopeKind.BUILTINS:
            continue
        for node in scope.nodes:
            pending: list[tuple[str, DependencyInput | None]] = [
                (occurrence.name, occurrence) for occurrence in node.inputs
                if isinstance(occurrence.name, str)
                and occurrence.access is not AccessMode.WRITE
                and occurrence.name in builtin_names
                and not _has_resolved_read(node, occurrence.name)
                and not (occurrence.is_callee and _has_resolved_call(node, occurrence.name))
                and not _has_source_binding(scope, occurrence.source or occurrence.name, node)
            ]
            if node in imported_calls:
                assert node.binding is not None
                pending.append((node.binding.removeprefix('builtins.'), None))
            for name, occurrence in pending:
                binding = next(
                    iter(builtin_scope.bindings.get(name, ())),
                    None,
                )
                if binding is None:
                    binding = NodeRecord(
                        name=name,
                        scope=builtin_scope,
                        kind=NodeKind.VARIABLE,
                        binding=name,
                    )
                    builtin_scope.nodes.append(binding)
                    builtin_scope.bindings[name] = [binding]
                    builtin_scope.defines.add(name)
                node.add_dependency(binding, occurrence, access=AccessMode.READ)
    if builtin_scope.nodes and builtin_scope not in scopes:
        root = next(scope for scope in scopes if scope.kind == ScopeKind.ROOT)
        builtin_scope.parent = root
        root.children.append(builtin_scope)
        scopes.append(builtin_scope)


def _has_source_binding(
    scope: ScopeRecord,
    name: str | Reference,
    before: NodeRecord | None,
) -> bool:
    source = name if isinstance(name, Reference) else None
    if source is None and before is not None:
        source = next(
            (occurrence.source for occurrence in before.inputs
             if occurrence.name == name and occurrence.source is not None),
            None,
        )
    position = None
    if source is not None and source.read_scope is not None:
        scope = source.read_scope
        name = source.description
        position = source.read_position
        before = None
    current: ScopeRecord | None = scope
    while current is not None:
        if name in current.global_decls:
            visible = current.find_nodes(
                source if source is not None and current is scope else name,
                before=before, position=position if current is scope else None,
            )
            return bool(visible) and not any(node.is_deletion for node in visible)
        if name in current.nonlocal_decls:
            return True
        if current.kind in (ScopeKind.FUNCTION, ScopeKind.COMPREHENSION) and name in current.defines:
            return True
        if current.kind == ScopeKind.CLASS:
            visible = current.find_nodes(
                source if source is not None and current is scope else name,
                before=before
                if before is not None and before.scope is current
                else None,
                position=position if current is scope else None,
            )
            if visible and not any(node.is_deletion for node in visible):
                return True
            if any(node.is_deletion for node in visible):
                if name in current.defines:
                    visible = current._find_enclosing_nodes(
                        name, eager=position is not None or before is not None,
                        environment=source.environment if source is not None else None,
                    )
                    return bool(visible) and not any(node.is_deletion for node in visible)
                current = current._find_lexical_parent()
                continue
            if name in current.defines:
                return False
        current = current._find_lexical_parent()
    visible = scope.find_nodes(source or name, before=before, position=position)
    return bool(visible) and not any(node.is_deletion for node in visible)


def remove_resolved_scope_bindings(scopes: list[ScopeRecord]) -> None:
    """Drop empty lexical binding nodes after their scopes are resolved.

    A function or class definition has both a scope and a module-level binding
    node.  Once name and call resolution has completed, the child scope is the
    useful graph entity and the empty binding node is only an implementation
    detail.  Keep binding nodes that carry declaration dependencies (for
    example, a decorator or a base class), since removing those would lose
    real graph edges. Keep declarations referenced by IR identities as nodes so
    the graph preserves which binding each dependency uses.
    """
    referenced_bindings = {
        name
        for scope in scopes
        for consumer in scope.nodes
        for name in consumer.raw_deps
        if isinstance(name, Reference)
    }
    removable_by_scope = {
        id(scope): [
            node
            for node in scope.nodes
            if _is_empty_scope_binding(node)
            and node.reference not in referenced_bindings
        ]
        for scope in scopes
    }
    removable_ids = {
        id(node)
        for nodes in removable_by_scope.values()
        for node in nodes
    }
    if not removable_ids:
        return
    for scope in scopes:
        removable = removable_by_scope[id(scope)]
        if not removable:
            continue
        scope.nodes[:] = [
            node for node in scope.nodes if id(node) not in removable_ids
        ]
        for node in removable:
            binding = node.binding
            if binding is None:
                continue
            definitions = scope.bindings.get(binding)
            if definitions is None:
                continue
            definitions[:] = [
                candidate
                for candidate in definitions
                if id(candidate) not in removable_ids
            ]
            if not definitions:
                del scope.bindings[binding]

    replacements = {}
    for scope in scopes:
        for node in removable_by_scope[id(scope)]:
            replacement = node.declared_scope
            assert replacement is not None  # Selected by _is_empty_scope_binding.
            replacements[id(node)] = replacement
    for scope in scopes:
        for node in scope.nodes:
            for dependency in tuple(node.deps):
                replacement = replacements.get(id(dependency))
                if replacement is None:
                    continue
                if (
                    isinstance(dependency, NodeRecord)
                    and dependency.binding is not None
                    and dependency.binding in node.raw_calls
                ):
                    # Callee outputs already feed the call. Preserve separate
                    # uses of the same declaration as an argument.
                    reads = node.collect_read_inputs()
                    if reads:
                        for occurrence in reads:
                            if occurrence.is_callee:
                                node.deps[dependency].pop(occurrence, None)
                    if not node.deps[dependency]:
                        del node.deps[dependency]
                        continue
                node.replace_dependency(dependency, replacement)


def _is_empty_scope_binding(node: NodeRecord) -> bool:
    if not node.kind.is_value and node.kind is not NodeKind.COMPREHENSION:
        return False
    if node.raw_deps or node.raw_calls:
        return False
    return node.declared_scope is not None
