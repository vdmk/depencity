"""Resolve dependencies between package scopes using collected import tables."""

from __future__ import annotations

import ast
from collections.abc import Iterable

from depencity._graph.ir_builder import (
    _add_call_targets,
    _add_constructor_targets,
    _attribute_receiver_path,
    _collect_resolution_counts,
    _find_alias_target,
    _find_call_member_path,
    _find_class_member_scopes,
    _find_class_object_targets,
    _find_member_value_bindings,
    _has_direct_member_write,
    _infer_binding_targets,
    _is_annotation_source_class,
    _is_empty_scope_binding,
    _is_name_deletion,
    _propagate_dependencies,
    _propagate_member_targets,
    _unresolved_node,
    _unwrap_class_object_annotation,
    _visible_types,
    finalize_resolved_ir,
    remove_resolved_scope_bindings,
    resolve,
)
from depencity._graph.model.enums import AccessMode, NodeKind, ScopeKind
from depencity._graph.model.ir import AnnotationHint, NodeRecord, ScopeRecord
from depencity._graph.model.reference import Reference


def resolve_package(
    scopes: list[ScopeRecord],
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    annotation_imports: set[NodeRecord],
) -> None:
    """Complete package IR before lowering; module discovery is already finished."""
    _resolve_package_dependencies(scopes, modules)
    remove_resolved_scope_bindings(scopes)
    shadowed_module_members = set()
    for scopes_in_module, imports in modules.values():
        for scope in scopes_in_module:
            for node in scope.nodes:
                for call_name in node.raw_calls:
                    receiver, member = _find_call_member_path(node, call_name)
                    if not member:
                        continue
                    for binding in node.find_bindings(receiver):
                        target_module, symbol = imports.get(binding, (None, None))
                        if not target_module or not symbol:
                            continue
                        child_module = f'{target_module}.{symbol}'
                        package = modules.get(target_module)
                        if not package or child_module not in modules:
                            continue
                        package_bindings = package[0][0].find_nodes(symbol)
                        if package_bindings and not all(
                            _is_imported_module(
                                candidate, child_module, package[1]
                            )
                            for candidate in package_bindings
                        ):
                            shadowed_module_members.add((binding, member))
    finalize_resolved_ir(scopes, annotation_imports, shadowed_module_members)


def _resolve_package_dependencies(
    records: list[ScopeRecord],
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
) -> None:
    """Complete source, import, and member facts over the same scope registry."""
    root = records[0]
    resolve(records)
    _resolve_internal_calls(modules)
    _resolve_import_targets(modules, root)
    _resolve_imported_attribute_reads(modules, root)
    while _propagate_dependencies(records):
        pass
    changed = True
    while changed:
        before = [
            _collect_resolution_counts(node) for scope in records for node in scope.nodes
        ]
        for scopes, imports in modules.values():
            for binding, (module_name, symbol) in imports.items():
                if symbol is None:
                    continue
                binding.callable_targets.update(
                    target for target in _find_exported_scopes(modules, module_name, symbol)
                    if target.kind == ScopeKind.FUNCTION
                )
        _resolve_internal_calls(modules)
        _resolve_imported_attribute_reads(modules, root)
        _propagate_dependencies(records)
        changed = before != [
            _collect_resolution_counts(node) for scope in records for node in scope.nodes
        ]
    _resolve_import_targets(modules, root)


def _visible_imports(
    name: str,
    node: NodeRecord,
    imports: dict[NodeRecord, tuple[str, str | None]],
) -> list[tuple[NodeRecord, tuple[str, str | None]]]:
    bindings = node.find_bindings(name)
    return [
        (binding, imports[binding])
        for binding in bindings
        if binding in imports
    ]


def _visible_annotation_imports(
    hint: AnnotationHint,
    imports: dict[NodeRecord, tuple[str, str | None]],
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
) -> list[tuple[str, str]]:
    expression = ast.parse(hint.name, mode='eval').body
    expression = _unwrap_class_object_annotation(hint, expression) or expression
    parts = hint.parse_class_name(expression)
    if not parts:
        return []
    bindings = hint.scope.find_nodes(
        parts[0], position=hint.position, environment=hint.environment,
    )
    if len(parts) > 1 and _has_direct_member_write(
        hint.scope, bindings, '.'.join(parts), None, position=hint.position,
    ):
        return []
    targets = []
    for binding in bindings:
        if binding not in imports:
            continue
        module_name, symbol = imports[binding]
        imported_module = (
            _find_imported_module_name(modules, module_name, symbol) if symbol else None
        )
        if imported_module in modules:
            module_name = imported_module
            symbol = None
        qualified_symbol = '.'.join(
            part for part in (symbol, *parts[1:]) if part
        )
        target_module = modules.get(module_name)
        if qualified_symbol and target_module is not None and any(
            _is_annotation_source_class(target, target_module[0][0])
            for target in _find_exported_scopes(
                modules, module_name, qualified_symbol
            )
        ):
            targets.append((module_name, qualified_symbol))
    return targets


def _is_imported_module(
    binding: NodeRecord,
    module_name: str,
    imports: dict[NodeRecord, tuple[str, str | None]],
) -> bool:
    if binding not in imports:
        return False
    imported_module, symbol = imports[binding]
    if symbol is None:
        return imported_module == module_name
    return f'{imported_module}.{symbol}' == module_name


def _find_visible_qualified_scopes(
    scope: ScopeRecord,
    qualified_name: str,
) -> list[ScopeRecord]:
    """Resolve a qualified name through the current binding versions."""
    candidates = []
    for binding, _ in _find_member_value_bindings(scope, qualified_name):
        if binding.declared_scope is not None:
            candidates.append(binding.declared_scope)
        candidates.extend(
            target for target in _find_class_object_targets(binding)
            if target not in candidates
        )
        candidates.extend(
            target for target in binding.callable_targets
            if target not in candidates
        )
    return sorted(candidates, key=_create_source_target_name)


def _find_exported_scopes(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    module_name: str,
    symbol: str,
    seen: set[tuple[str, str]] | None = None,
) -> list[ScopeRecord]:
    seen = set() if seen is None else seen
    key = (module_name, symbol)
    if key in seen:
        return []
    seen.add(key)
    prefix, separator, suffix = symbol.partition('.')
    if separator:
        child_module = _find_imported_module_name(modules, module_name, prefix)
        if child_module is not None and _has_source_module(modules, child_module):
            return _find_exported_scopes(modules, child_module, suffix, seen)
    if module_name not in modules:
        return []
    scopes, imports = modules[module_name]
    module_scope = scopes[0]
    candidates = _find_visible_qualified_scopes(module_scope, symbol)

    parts = symbol.split('.')
    for prefix_length in range(1, len(parts) + 1):
        prefix = '.'.join(parts[:prefix_length])
        suffix = '.'.join(parts[prefix_length:])
        for binding in module_scope.find_nodes(prefix):
            target = imports.get(binding)
            if target is None:
                continue
            forwarded_symbol = '.'.join(
                part for part in (target[1], suffix) if part
            )
            if not forwarded_symbol:
                continue
            candidates.extend(
                candidate
                for candidate in _find_exported_scopes(
                    modules, target[0], forwarded_symbol, seen
                )
                if candidate not in candidates
            )
    return candidates


def _captured_import_targets(
    scope: ScopeRecord,
    node: NodeRecord,
    imports: dict[NodeRecord, tuple[str, str | None]],
) -> list[tuple[str, str | None]]:
    targets = []
    for reference in node.raw_callee_deps:
        for callee in scope.find_nodes(reference, before=node):
            if callee.attribute_expression is None:
                continue
            receiver_name = _attribute_receiver_path(
                callee.attribute_expression
            )[0]
            for binding in callee.find_bindings(receiver_name):
                target = imports.get(binding) or (
                    imports.get(alias) if (alias := _find_alias_target(binding)) is not None else None
                )
                if target is not None and target not in targets:
                    targets.append(target)
    return targets


def _resolve_internal_calls(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
) -> None:
    _propagate_import_aliases(modules)
    target_symbol: str | None
    import_targets = {
        binding: target
        for _, imports in modules.values()
        for binding, target in imports.items()
    }
    for module_name, (scopes, imports) in modules.items():
        root_scope = scopes[0].parent
        if root_scope is None:
            continue
        for scope in scopes:
            for node in scope.nodes:
                if not node.raw_calls:
                    continue
                if not node.is_dynamic_call:
                    for call_name in node.raw_calls:
                        bindings = (
                            [
                                binding
                                for reference in node.raw_callee_deps
                                for binding in scope.find_nodes(
                                    reference, before=node
                                )
                            ]
                            if node.raw_callee_deps
                            else node.find_bindings(call_name)
                        )
                        for binding in bindings:
                            class_scope = binding.declared_scope
                            if class_scope is not None and class_scope.kind == ScopeKind.CLASS:
                                _add_constructor_targets(node, class_scope)
                for call_name in node.raw_calls:
                    call_root, member_path = _find_call_member_path(node, call_name)
                    captured_targets = _captured_import_targets(
                        scope, node, imports
                    )
                    assigned_import_alias = any(
                        not binding.is_import
                        for binding, target in _visible_imports(
                            call_root, node, imports
                        )
                    )
                    if member_path:
                        if _has_direct_member_write(
                            scope,
                            node.find_bindings(call_root),
                            call_name,
                            node,
                        ):
                            continue
                        typed_targets = sorted({
                            (target, member_path)
                            for type_name in _visible_types(scope, call_root, node)
                            for target in _visible_annotation_imports(
                                type_name, import_targets, modules
                            )
                        })
                        resolved_typed_target = False
                        for (
                            target_module_name,
                            target_symbol,
                        ), member in typed_targets:
                            target_module = modules.get(target_module_name)
                            if target_module is None:
                                continue
                            if target_module[0][0].is_package_initializer:
                                target_scopes = _find_exported_scopes(
                                    modules, target_module_name,
                                    f'{target_symbol}.{member}',
                                )
                            else:
                                target_scopes = _find_visible_qualified_scopes(
                                    target_module[0][0],
                                    f'{target_symbol}.{member}',
                                )
                            for target_scope in target_scopes:
                                if target_scope.kind == ScopeKind.FUNCTION:
                                    _add_call_targets(node, target_scope)
                                if target_scope.kind == ScopeKind.CLASS:
                                    node.resolved_class_targets.add(target_scope)
                                    _add_constructor_targets(node, target_scope)
                                target_node = _add_import_target_value(
                                    root_scope,
                                    f'{target_module_name}.{target_symbol}.{member}',
                                    target_scope,
                                )
                                node.resolved_import_targets.add(target_node)
                                resolved_typed_target = True
                        if resolved_typed_target:
                            continue
                    imported = _visible_imports(call_root, node, imports)
                    targets = captured_targets or [
                        target for _, target in imported
                    ]

                    for target_module_name, target_symbol in targets:
                        package = modules.get(target_module_name)
                        child_module_name = (
                            f'{target_module_name}.{target_symbol}'
                            if target_symbol
                            else None
                        )
                        if member_path and package and child_module_name in modules:
                            assert target_symbol is not None
                            bindings = package[0][0].find_nodes(target_symbol)
                            if bindings and not all(
                                _is_imported_module(
                                    binding, child_module_name, package[1]
                                )
                                for binding in bindings
                            ):
                                continue
                        resolved_symbol = target_symbol
                        if member_path:
                            resolved_symbol = (
                                f'{resolved_symbol}.{member_path}'
                                if resolved_symbol
                                else member_path
                            )

                        if resolved_symbol is not None:
                            target_scopes = _find_exported_scopes(
                                modules, target_module_name, resolved_symbol,
                            )
                        elif target_module_name in modules:
                            target_scopes = [modules[target_module_name][0][0]]
                        else:
                            continue
                        for target_scope in target_scopes:
                            if target_scope.kind == ScopeKind.FUNCTION:
                                _add_call_targets(node, target_scope)
                            if target_scope.kind == ScopeKind.CLASS:
                                node.resolved_class_targets.add(target_scope)
                                _add_constructor_targets(node, target_scope)
                            if target_scope is scope:
                                continue
                            canonical = target_module_name
                            if resolved_symbol is not None:
                                canonical = f'{canonical}.{resolved_symbol}'
                            target_node = _add_import_target_value(
                                root_scope, canonical, target_scope
                            )
                            # Bare aliases already carry their imported target.
                            if assigned_import_alias and member_path:
                                node.resolved_import_targets.add(target_node)
                        if not target_scopes:
                            continue

    for scopes, _ in modules.values():
        for scope in scopes:
            for node in scope.nodes:
                _infer_binding_targets(node)
    _resolve_imported_callable_aliases(modules, import_targets)
    _resolve_inferred_import_member_calls(modules)


def _propagate_import_aliases(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
) -> None:
    for _, imports in modules.values():
        for node, (target_module, symbol) in tuple(imports.items()):
            submodule = f'{target_module}.{symbol}' if symbol else None
            package_scopes, package_imports = modules.get(target_module, ([], {}))
            package_bindings = (
                package_scopes[0].find_nodes(symbol or '') if package_scopes else []
            )
            if submodule is not None and _has_source_module(modules, submodule) and all(
                _is_imported_module(binding, submodule, package_imports)
                for binding in package_bindings
            ):
                imports[node] = (submodule, None)
    for scopes, imports in modules.values():
        for scope in scopes:
            for node in scope.nodes:
                if node in imports or node.is_import or node.binding is None:
                    continue
                alias = _find_alias_target(node)
                imported_module = imports.get(alias) if alias is not None else None
                if imported_module is None or not _has_source_module(modules, imported_module[0]):
                    continue
                imported_classes = (
                    _find_exported_scopes(
                        modules, imported_module[0], imported_module[1]
                    )
                    if imported_module[1] is not None
                    else []
                )
                if imported_module[1] is None or any(
                    target.kind == ScopeKind.CLASS for target in imported_classes
                ):
                    imports[node] = imported_module


def _resolve_imported_callable_aliases(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    imports: dict[NodeRecord, tuple[str, str | None]],
) -> None:
    for scopes, _ in modules.values():
        for scope in scopes:
            for node in scope.nodes:
                if not node.raw_calls:
                    continue
                for call_name in node.raw_calls:
                    if '.' in call_name and not node.is_dynamic_call:
                        continue
                    bindings = [
                        binding
                        for reference in node.raw_callee_deps or [call_name]
                        for binding in scope.find_nodes(reference, before=node)
                    ]
                    for binding in bindings:
                        if binding.is_import:
                            continue
                        origin = _find_alias_target(binding)
                        for target in _find_callable_import_targets(binding, modules, imports):
                            if isinstance(target, ScopeRecord):
                                if target.kind == ScopeKind.FUNCTION:
                                    _add_call_targets(node, target)
                                continue
                            elif origin is not None and origin.is_import:
                                continue
                            node.resolved_import_targets.add(target)


def _create_source_target_name(scope: ScopeRecord) -> str:
    """Name a declaration independently of its exported aliases."""
    parts = []
    while scope.kind != ScopeKind.MODULE:
        parent = scope.parent
        assert parent is not None  # Source declarations belong to a module.
        siblings = [child for child in parent.children if child.name == scope.name]
        name = scope.name
        if len(siblings) > 1:
            name = f'{name}#{siblings.index(scope) + 1}'
        parts.append(name)
        scope = parent
    return '.'.join([scope.name, *reversed(parts)])


def _find_callable_import_targets(
    binding: NodeRecord,
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    imports: dict[NodeRecord, tuple[str, str | None]],
    seen: set[int] | None = None,
) -> list[NodeRecord | ScopeRecord]:
    seen = set() if seen is None else seen
    if (
        binding.declared_scope is not None
        or binding.binding is None and not binding.value_sources
        or id(binding) in seen
    ):
        return []
    seen.add(id(binding))
    targets: list[NodeRecord | ScopeRecord] = []
    imported = imports.get(binding)
    if imported is not None:
        target_module, symbol = imported
        if symbol is not None and target_module in modules:
            targets.extend(
                target
                for target in _find_exported_scopes(
                    modules, target_module, symbol
                )
                if target.kind == ScopeKind.FUNCTION and target not in targets
            )
        elif target_module not in modules:
            targets.extend(
                dependency
                for dependency in binding.deps
                if isinstance(dependency, NodeRecord)
                and dependency.scope.kind == ScopeKind.ROOT
                and dependency not in targets
            )
    dependencies = (
        [
            dependency
            for source in binding.value_sources
            for dependency in binding.scope.find_nodes(source, before=binding)
        ]
        if binding.value_sources
        else binding.deps
    )
    for dependency in dependencies:
        if isinstance(dependency, NodeRecord) and (
            dependency.is_import
            or dependency.value_sources
            or (dependency.binding is not None and dependency.access is not None)
        ):
            targets.extend(
                target
                for target in _find_callable_import_targets(
                    dependency, modules, imports, seen
                )
                if target not in targets
            )
    return targets


def _resolve_inferred_import_member_calls(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
) -> None:
    for module_name, (scopes, _) in modules.items():
        root_scope = scopes[0].parent
        if root_scope is None:
            continue
        for scope in scopes:
            for node in scope.nodes:
                if not node.raw_calls or node.is_dynamic_call:
                    continue
                for call_name in node.raw_calls:
                    receiver, member_path = _find_call_member_path(node, call_name)
                    if not member_path:
                        continue
                    bindings = node.find_bindings(receiver)
                    if _has_direct_member_write(scope, bindings, call_name, node):
                        continue
                    for binding in bindings:
                        imported = _find_alias_target(binding)
                        if imported is not None and imported.is_import and not binding.inferred_classes:
                            continue
                        for class_scope in sorted(
                            binding.class_object_targets | binding.inferred_classes,
                            key=_create_source_target_name,
                        ):
                            class_module = class_scope.parent
                            if (
                                class_module is None
                                or class_module.kind != ScopeKind.MODULE
                                or class_module.name == module_name
                            ):
                                continue
                            for member_scope in _find_class_member_scopes(class_scope, member_path):
                                canonical = (
                                    f'{class_module.name}.{class_scope.symbol}.'
                                    f'{member_path}'
                                )
                                if member_scope.kind == ScopeKind.FUNCTION:
                                    _add_call_targets(node, member_scope)
                                if member_scope.kind == ScopeKind.CLASS:
                                    node.resolved_class_targets.add(member_scope)
                                    _add_constructor_targets(node, member_scope)
                                target = _add_import_target_value(
                                    root_scope, canonical, member_scope
                                )
                                node.resolved_import_targets.add(target)


def _resolve_import_targets(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    root: ScopeRecord,
) -> None:
    """Connect canonical targets before declaration bindings are removed."""
    for scopes, imports in modules.values():
        for scope in scopes:
            for node in scope.nodes:
                if not node.is_import or node not in imports:
                    continue
                target_module_name, target_symbol = imports[node]
                target_module = modules.get(target_module_name)
                if target_module is None:
                    continue
                canonical = target_module_name
                if target_symbol is None:
                    _add_import_target_value(root, canonical, target_module[0][0])
                    continue

                canonical = f'{canonical}.{target_symbol}'
                current_bindings = [
                    binding for binding in target_module[0][0].find_nodes(target_symbol)
                    if not _is_name_deletion(binding)
                ]
                declared_scopes = [
                    binding.declared_scope
                    for binding in current_bindings
                    if binding.declared_scope is not None
                ]
                declared_scopes.extend(
                    target for target in _find_exported_scopes(
                        modules, target_module_name, target_symbol
                    )
                    if target.kind in (ScopeKind.CLASS, ScopeKind.FUNCTION)
                    and target not in declared_scopes
                )
                for target_scope in declared_scopes:
                    _add_import_target_value(root, canonical, target_scope)
                if declared_scopes:
                    target_node = root.bindings[canonical][0]
                    for binding in current_bindings:
                        if binding.declared_scope is None:
                            target_node.add_dependency(binding, access=AccessMode.READ)
                    if current_bindings and all(
                        (origin := _find_alias_target(binding)) is not None and origin.is_import
                        for binding in current_bindings
                    ):
                        # Re-export imports already carry their callable identity.
                        for binding in current_bindings:
                            for dependency in binding.collect_forwarded_dependencies(target_node):
                                if dependency not in current_bindings:
                                    target_node.deps.pop(dependency, None)
                    # Alias bindings already carry the source declaration.
                    for target_scope in declared_scopes:
                        assert target_scope.parent is not None
                        if not any(
                            binding.declared_scope is target_scope
                            for binding in current_bindings
                        ):
                            target_node.deps.pop(target_scope, None)
                            if current_bindings:
                                for declaration in target_scope.parent.nodes:
                                    if declaration.declared_scope is target_scope:
                                        target_node.deps.pop(declaration, None)
                    continue

                if current_bindings:
                    _add_import_target_dependencies(root, canonical, current_bindings)
                    continue
                target_submodule = modules.get(canonical)
                if target_submodule is not None:
                    _add_import_target_value(root, canonical, target_submodule[0][0])


def _resolve_imported_attribute_reads(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    root: ScopeRecord,
) -> None:
    for scopes, imports in modules.values():
        for scope in scopes:
            unresolved_by_name: dict[str | Reference, NodeRecord] = {}
            for node in scope.nodes:
                if node.is_unresolved:
                    assert node.binding is not None
                    unresolved_by_name[node.binding] = node
            for node in scope.nodes:
                if (
                    node.kind != NodeKind.REFERENCE
                    or node.access != AccessMode.READ
                    or node.attribute_expression is None
                ):
                    continue
                imported_name, member = _attribute_receiver_path(
                    node.attribute_expression
                )
                if node.access == AccessMode.READ and _has_direct_member_write(
                    scope, node.find_bindings(imported_name), node.attribute_expression, node,
                ):
                    continue
                for imported, (module_name, symbol) in _visible_imports(
                    imported_name, node, imports
                ):
                    internal_module_name = _find_imported_module_name(
                        modules, module_name, symbol,
                    )
                    forwarded = {
                        dependency for receiver in node.deps
                        if isinstance(receiver, NodeRecord)
                        for dependency in receiver.collect_forwarded_dependencies()
                    }
                    if internal_module_name is None:
                        package = modules.get(module_name)
                        if package and f'{module_name}.{symbol}' in modules:
                            assert symbol is not None
                            for binding in package[0][0].find_nodes(symbol):
                                if binding not in forwarded:
                                    node.add_dependency(binding, access=AccessMode.READ)
                        continue
                    parts = member.split('.')
                    for part in parts[:-1]:
                        child_module_name = _find_imported_module_name(
                            modules, internal_module_name, part,
                        )
                        if child_module_name is None:
                            package = modules.get(internal_module_name)
                            if package and f'{internal_module_name}.{part}' in modules:
                                for binding in package[0][0].find_nodes(part):
                                    if binding not in forwarded:
                                        node.add_dependency(binding, access=AccessMode.READ)
                            break
                        internal_module_name = child_module_name
                    else:
                        internal_module = modules.get(internal_module_name)
                        if internal_module is None:
                            continue
                        final_member = parts[-1]
                        bindings = internal_module[0][0].find_nodes(final_member)
                        if not bindings:
                            continue
                        live_bindings = [
                            binding for binding in bindings
                            if not _is_name_deletion(binding)
                        ]
                        if len(live_bindings) != len(bindings):
                            node.add_dependency(
                                _unresolved_node(
                                    scope,
                                    unresolved_by_name,
                                    ast.unparse(node.attribute_expression),
                                ),
                                access=node.access,
                            )
                        bindings = live_bindings
                        if not bindings:
                            continue
                        if any(
                            call.kind == NodeKind.CALL
                            and node.reference in call.raw_callee_deps
                            for call in scope.nodes
                        ):
                            bindings = [
                                binding for binding in bindings
                                if not _is_empty_scope_binding(binding)
                            ]
                            if not bindings:
                                continue
                        child_module_name = f'{internal_module_name}.{final_member}'
                        if child_module_name in modules and not all(
                            _is_imported_module(
                                binding,
                                child_module_name,
                                internal_module[1],
                            )
                            for binding in bindings
                        ):
                            for binding in bindings:
                                node.add_dependency(binding, access=node.access)
                                if node.access == AccessMode.READ:
                                    _propagate_member_targets(node, binding)
                            continue
                        canonical = f'{internal_module_name}.{final_member}'
                        target = _add_import_target_dependencies(
                            root, canonical, bindings
                        )
                        if node.access == AccessMode.READ:
                            for binding in bindings:
                                _propagate_member_targets(node, binding)
                        # This edge addresses the member itself. Receiver and
                        # value operands retain their separately collected reads.
                        node.add_dependency(target, access=node.access)


def _has_source_module(modules: dict, module_name: str) -> bool:
    return module_name in modules or any(
        name.startswith(f'{module_name}.') for name in modules
    )


def _find_imported_module_name(
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ],
    module_name: str,
    symbol: str | None,
    seen: set[tuple[str, str]] | None = None,
) -> str | None:
    """Follow a uniquely bound module alias without bypassing real members."""
    if symbol is None:
        return module_name
    seen = set() if seen is None else seen
    key = (module_name, symbol)
    if key in seen:
        return None
    seen.add(key)
    scopes, imports = modules.get(module_name, ([], {}))
    bindings = scopes[0].find_nodes(symbol) if scopes else []
    if not bindings:
        submodule = f'{module_name}.{symbol}'
        return submodule if _has_source_module(modules, submodule) else None
    targets = set()
    for binding in bindings:
        target = imports.get(binding) or (
            imports.get(alias) if (alias := _find_alias_target(binding)) is not None else None
        )
        if target is None:
            return None
        targets.add(target)
    if len(targets) != 1:
        return None
    target_module, target_symbol = next(iter(targets))
    return _find_imported_module_name(modules, target_module, target_symbol, seen)


def _add_import_target_value(
    root: ScopeRecord,
    canonical: str,
    target_scope: ScopeRecord,
) -> NodeRecord:
    assert target_scope.parent is not None
    target = _add_import_target_dependencies(
        root, canonical, [
            binding for binding in target_scope.parent.nodes
            if binding.declared_scope is target_scope
            and not _is_empty_scope_binding(binding)
        ] or [target_scope]
    )
    if target_scope.kind == ScopeKind.CLASS:
        target.class_object_targets.add(target_scope)
    elif target_scope.kind == ScopeKind.FUNCTION:
        target.callable_targets.add(target_scope)
    return target


def _add_import_target_dependencies(
    root: ScopeRecord,
    canonical: str,
    dependencies: Iterable[NodeRecord | ScopeRecord],
) -> NodeRecord:
    targets = root.bindings.get(canonical)
    if targets is None:
        target = NodeRecord(
            canonical, root, kind=NodeKind.IMPORT_TARGET, binding=canonical,
        )
        root.nodes.append(target)
        targets = root.bindings[canonical] = [target]
    for dependency in dependencies:
        targets[0].add_dependency(dependency, access=AccessMode.READ)
    return targets[0]
