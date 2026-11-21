"""Discover package sources and construct module IR with import context."""

from __future__ import annotations

import ast
import tokenize
from pathlib import Path
from typing import cast

from depencity._graph.graph_builder import lower
from depencity._graph.ir_builder import (
    _attribute_receiver_path,
    _collect_annotation_import_names,
    _find_alias_target,
    build_resolved_ir,
)
from depencity._graph.model.enums import AccessMode, ScopeKind
from depencity._graph.model.ir import NodeRecord, ScopeRecord
from depencity._graph.model.scope import Scope
from depencity._graph.scope_builder import (
    _collect_literal_exports,
    build_ir,
    collect_used_imports,
    prune_unused_imports,
)
from depencity._package_graph.resolver import resolve_package

_IGNORED_DIRECTORIES = {
    '.git',
    '.idea',
    '.mypy_cache',
    '.nox',
    '.pytest_cache',
    '.ruff_cache',
    '.venv',
    '__pycache__',
    'env',
    'node_modules',
    'venv',
}


def _read_python_source(path: Path) -> str:
    if path.is_symlink():
        raise ValueError(f'source file symlinks are not supported: {path.name}')
    with tokenize.open(path) as source_file:
        return source_file.read()


def _module_name(relative_path: Path, package_name: str) -> str:
    parts = relative_path.with_suffix('').parts
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join((package_name, *parts)) if parts else package_name


def _relative_module(package_name: str, level: int, imported: str | None) -> str:
    package_parts = [] if level == 0 else package_name.split('.')
    if level > len(package_parts):
        return '.' * (level - len(package_parts)) + (imported or '')
    if level > 1:
        package_parts = package_parts[:-(level - 1)]
    if imported:
        package_parts.append(imported)
    return '.'.join(package_parts)


def _collect_import_targets(
    tree: ast.Module,
    package_name: str,
    module_scope: ScopeRecord,
) -> dict[NodeRecord, tuple[str, str | None]]:
    result: dict[NodeRecord, tuple[str, str | None]] = {}
    import_nodes = {
        scope: [node for node in scope.nodes if node.is_import]
        for scope in _walk_scopes(module_scope)
    }

    class ImportCollector(ast.NodeVisitor):
        scope = module_scope

        def visit_Import(self, node: ast.Import) -> None:
            targets = []
            for alias in node.names:
                binding = alias.asname or alias.name.split('.')[0]
                imported = alias.name if alias.asname else binding
                module, separator, symbol = imported.rpartition('.')
                target = (module, symbol) if separator else (imported, None)
                targets.append((binding, target, _span(node)))
            self._record(targets)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            base = _relative_module(package_name, node.level, node.module)
            self._record(
                (alias.asname or alias.name, (base, alias.name), _span(node))
                for alias in node.names
                if alias.name != '*'
            )

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_scope(node, ScopeKind.FUNCTION)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_scope(node, ScopeKind.FUNCTION)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self._visit_scope(node, ScopeKind.CLASS)

        def _visit_scope(
            self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
            kind: ScopeKind,
        ) -> None:
            parent = self.scope
            span = _span(node)
            child = next(
                child for child in parent.children
                if child.kind == kind and child.span == span
            )
            self.scope = child
            for statement in node.body:
                self.visit(statement)
            self.scope = parent

        def _record(self, targets) -> None:
            nodes = import_nodes[self.scope]
            for name, target, span in targets:
                imported = next(
                    (
                        candidate for candidate in nodes
                        if candidate.binding == name and candidate.span == span
                        and candidate not in result
                    ),
                    None,
                )
                if imported is not None:
                    result[imported] = target

    ImportCollector().visit(tree)
    return result


def _walk_scopes(scope: ScopeRecord):
    pending = [scope]
    while pending:
        current = pending.pop()
        yield current
        pending.extend(current.children)


def _span(node: ast.stmt) -> tuple[int, int, int, int]:
    # Import collection only visits parsed statements with complete locations.
    return cast(tuple[int, int, int, int], (
        node.lineno,
        node.col_offset,
        getattr(node, 'end_lineno', node.lineno),
        getattr(node, 'end_col_offset', node.col_offset),
    ))


def _module_exports(
    tree: ast.Module,
    package_name: str | None = None,
    available_exports: dict[str, tuple[set[str], bool]] | None = None,
) -> tuple[set[str], bool]:
    """Collect possible star exports and whether additional names are unknown."""
    explicit = _collect_literal_exports(tree)
    names = set()
    unknown_exports = False

    class BindingCollector(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            names.add(node.name)
            for expression in node.decorator_list:
                self.visit(expression)
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            for expression in (*node.decorator_list, *node.bases):
                self.visit(expression)
            for keyword in node.keywords:
                self.visit(keyword.value)
            names.add(node.name)

        def visit_TypeAlias(self, node: ast.TypeAlias) -> None:
            if isinstance(node.name, ast.Name):
                names.add(node.name.id)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.type is not None:
                self.visit(node.type)
            had_prior_binding = node.name in names
            for statement in node.body:
                self.visit(statement)
            if node.name and not had_prior_binding:
                names.discard(node.name)

        def visit_MatchAs(self, node: ast.MatchAs) -> None:
            if node.name:
                names.add(node.name)
            self.generic_visit(node)

        def visit_MatchStar(self, node: ast.MatchStar) -> None:
            if node.name:
                names.add(node.name)
            self.generic_visit(node)

        def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
            if node.rest:
                names.add(node.rest)
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            names.update(
                alias.asname or alias.name.split('.')[0] for alias in node.names
            )

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            names.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name != '*'
            )

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Store):
                names.add(node.id)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if node.value is not None or not isinstance(node.target, ast.Name):
                self.visit(node.target)
            if node.value is not None:
                self.visit(node.value)

        def visit_comprehension(self, node: ast.comprehension) -> None:
            self.visit(node.iter)
            for condition in node.ifs:
                self.visit(condition)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            for expression in (*node.args.defaults, *node.args.kw_defaults):
                if expression is not None:
                    self.visit(expression)

    collector = BindingCollector()
    for statement in tree.body:
        if package_name is not None and available_exports is not None:
            statement_tree = ast.Module(body=[statement], type_ignores=[])
            for imported in _collect_module_imports(statement_tree):
                if not any(alias.name == '*' for alias in imported.names):
                    continue
                target_module = _relative_module(
                    package_name, imported.level, imported.module
                )
                imported_exports, unknown = available_exports.get(
                    target_module, (set(), True)
                )
                unknown_exports |= unknown
                names.update(imported_exports)
        collector.visit(statement)
        names.difference_update(_unconditional_module_deletions(statement))
    if explicit is not None:
        return explicit, False
    return {
        name for name in names if not name.startswith('_')
    }, '__all__' in names or unknown_exports


def _unconditional_module_deletions(statement: ast.stmt) -> set[str]:
    if isinstance(statement, ast.Delete):
        return {
            target.id
            for expression in statement.targets
            for target in ast.walk(expression)
            if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Del)
        }
    return set()


def _collect_module_imports(tree: ast.Module) -> list[ast.ImportFrom]:
    imports = []

    class ModuleImportCollector(ast.NodeVisitor):
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            imports.append(node)

        def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            return

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

    ModuleImportCollector().visit(tree)
    return imports


def _collect_package_import_retention(
    modules: dict[str, tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]]],
    retained_imports: set[NodeRecord],
) -> set[NodeRecord]:
    """Retain re-exports through the same lexical bindings used by the graph."""
    binding: NodeRecord | None
    pending = []
    for records, imports in modules.values():
        for binding in collect_used_imports(records) | (retained_imports & imports.keys()):
            target_module, symbol = imports[binding]
            if symbol is not None:
                pending.append(f'{target_module}.{symbol}')
        for scope in records:
            for node in scope.nodes:
                if node.attribute_expression is None or node.access != AccessMode.READ:
                    continue
                receiver, member_path = _attribute_receiver_path(node.attribute_expression)
                if not receiver.isidentifier():
                    continue
                for receiver_binding in node.find_bindings(receiver):
                    binding = _find_alias_target(receiver_binding)
                    if binding is not None and binding in imports:
                        target_module, symbol = imports[binding]
                        if symbol is not None:
                            canonical = f'{target_module}.{symbol}'
                        else:
                            target = next(iter(binding.deps))
                            assert isinstance(target, NodeRecord) and target.binding is not None
                            canonical = target.binding
                        pending.append(f'{canonical}.{member_path}')

    seen = set()
    while pending:
        qualified_name = pending.pop()
        if qualified_name in seen:
            continue
        seen.add(qualified_name)
        parts = qualified_name.split('.')
        for index in range(len(parts) - 1, 0, -1):
            module_name = '.'.join(parts[:index])
            if module_name not in modules:
                continue
            records, imports = modules[module_name]
            for binding in records[1].find_current_nodes(parts[index]):
                binding = _find_alias_target(binding)
                if binding is None or binding not in imports:
                    continue
                retained_imports.add(binding)
                target_module, symbol = imports[binding]
                if symbol is not None:
                    canonical = f'{target_module}.{symbol}'
                else:
                    target = next(iter(binding.deps))
                    assert isinstance(target, NodeRecord) and target.binding is not None
                    canonical = target.binding
                pending.append('.'.join((canonical, *parts[index + 1:])))
            break
    return retained_imports


def _expand_star_imports(
    tree: ast.Module,
    package_name: str,
    exports: dict[str, tuple[set[str], bool]],
) -> None:
    for statement in _collect_module_imports(tree):
        if not any(alias.name == '*' for alias in statement.names):
            continue
        module_name = _relative_module(
            package_name, statement.level, statement.module
        )
        names, unknown = exports.get(module_name, (set(), True))
        statement.names = [ast.alias(name=name) for name in sorted(names)]
        if unknown:
            statement.names.append(ast.alias(name='*'))


def build_package(
    root: str | Path,
    package_name: str | None = None,
    source: str | Path = '.',
) -> Scope:
    """Build and resolve one Python source root, returning its graph root."""
    root = Path(root).resolve()
    package_name = package_name or root.name
    graph_root = ScopeRecord('__root__', ScopeKind.ROOT)
    scopes: list[ScopeRecord] = [graph_root]
    modules: dict[
        str,
        tuple[list[ScopeRecord], dict[NodeRecord, tuple[str, str | None]]],
    ] = {}
    annotation_imports: set[NodeRecord] = set()

    source_root = (root / Path(source)).resolve()
    try:
        source_root.relative_to(root)
    except ValueError as error:
        raise ValueError(f'source must be inside package root: {source_root}') from error
    if not source_root.is_dir():
        raise ValueError(f'source directory does not exist: {source_root}')

    discovered_files: list[Path] = []
    module_paths: dict[str, Path] = {}
    trees = {}
    packages = {}
    def raise_discovery_error(error: OSError) -> None:
        raise error

    for directory, directories, filenames in source_root.walk(
        on_error=raise_discovery_error, follow_symlinks=False,
    ):
        directories[:] = [name for name in directories if name not in _IGNORED_DIRECTORIES]
        discovered_files.extend(directory / name for name in filenames if name.endswith('.py'))
    source_files = []
    for path in sorted(discovered_files, key=lambda path: path.parts):
        relative_path = path.relative_to(source_root)
        if path.is_dir():
            continue
        resolved_path = path.resolve()
        try:
            resolved_path.relative_to(source_root)
        except ValueError as error:
            raise ValueError(
                f'source file must be inside source directory: {resolved_path}'
            ) from error
        if path.is_symlink():
            raise ValueError(
                f'source file symlinks are not supported: {relative_path.as_posix()}'
            )
        if not path.is_file():
            continue
        module_name = _module_name(relative_path, package_name)
        if module_name in module_paths:
            raise ValueError(
                f'duplicate module name {module_name!r}: '
                f'{module_paths[module_name].as_posix()} and {relative_path.as_posix()}'
            )
        module_paths[module_name] = relative_path
        tree = ast.parse(_read_python_source(path), filename=str(path))
        module_package = (
            module_name
            if relative_path.name == '__init__.py'
            else module_name.rpartition('.')[0]
        )
        source_files.append((path, relative_path, module_name, module_package))
        trees[module_name] = tree
        packages[module_name] = module_package

    exports = {name: _module_exports(tree) for name, tree in trees.items()}
    for _ in range(len(trees)):
        updated_exports = {
            module_name: _module_exports(tree, packages[module_name], exports)
            for module_name, tree in trees.items()
        }
        if updated_exports == exports:
            break
        exports = updated_exports

    for _, _, module_name, module_package in source_files:
        _expand_star_imports(
            trees[module_name], module_package, exports
        )

    retained_imports: set[NodeRecord] = set()
    for path, relative_path, module_name, module_package in source_files:
        tree = trees[module_name]
        file_scopes = build_ir(tree, retain_unused_imports=True)
        module = file_scopes[1]
        imports = _collect_import_targets(tree, module_package, module)
        modules[module_name] = (file_scopes, imports)
        retained_names = _collect_literal_exports(tree) or set()
        if relative_path.name == '__init__.py':
            retained_names.update(exports[module_name][0])
        retained_imports.update(
            binding for name in retained_names
            for binding in module.find_current_nodes(name)
            if binding.is_import
        )

    retained_imports = _collect_package_import_retention(modules, retained_imports)
    for path, relative_path, module_name, module_package in source_files:
        tree = trees[module_name]
        file_scopes, import_targets = modules[module_name]
        annotation_names = _collect_annotation_import_names(tree)
        metadata_imports = {
            node for node in import_targets
            if node.binding in annotation_names
            and node in node.scope.find_current_nodes(node.binding)
        }
        prune_unused_imports(file_scopes, retained_imports | metadata_imports)
        import_targets = {
            node: target for node, target in import_targets.items()
            if node in node.scope.nodes
        }
        file_root = file_scopes.pop(0)
        module = file_scopes[0]
        module.name = module_name
        module.symbol = module_name
        module.is_standalone_module = False
        module.is_package_initializer = relative_path.name == '__init__.py'
        module.parent = graph_root
        graph_root.children.append(module)
        replacements = {}
        for target in file_root.nodes:
            canonical = target.binding
            assert canonical is not None  # Root nodes are named import targets.
            if canonical.startswith('.'):
                level = len(canonical) - len(canonical.lstrip('.'))
                canonical = _relative_module(
                    module_package, level, canonical[level:]
                )
            targets = graph_root.bindings.get(canonical)
            if targets is None:
                target.scope = graph_root
                target.binding = canonical
                target.name = canonical
                graph_root.nodes.append(target)
                targets = graph_root.bindings[canonical] = [target]
            replacements[id(target)] = targets[0]
        for scope in file_scopes:
            for node in scope.nodes:
                for dependency in tuple(node.deps):
                    replacement = replacements.get(id(dependency))
                    if replacement is not None:
                        node.replace_dependency(dependency, replacement)
        annotation_imports.update(
            node
            for node in import_targets
            if node.binding in annotation_names
            and node not in retained_imports
        )
        modules[module_name] = (file_scopes, import_targets)
        scopes.extend(file_scopes)

    resolve_package(scopes, modules, annotation_imports)
    return lower(scopes)


def build_target(path: str | Path, source: str | Path = '.') -> Scope:
    """Build and resolve a file or package target, returning its graph root."""
    path = Path(path)
    if path.is_dir():
        return build_package(path, source=source)
    return lower(build_resolved_ir(ast.parse(_read_python_source(path), filename=str(path))))
