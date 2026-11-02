import json
import sys
from pathlib import Path

import pytest

from depencity import build_package, build_target, summarize, to_dot, to_json
from depencity.mcp import profile

from .utils import (
    FIXTURES_ROOT,
    assert_fixture_sources_compile,
    assert_graph_integrity,
    read_fixture,
)


@pytest.mark.parametrize(
    "case",
    (
        "internal_calls",
        "computed_call_paths",
        "private_names",
        "builtins",
        "function_argument_call_targets",
        "external_call_target_population",
        "external_calls",
        "unresolved_targets",
        "external_aliases",
        "module_calls",
        "module_self_reexport",
        "module_value_reexports",
        "callable_reexport",
        "resolution_completion",
        "generator_calls",
        "relative_imports",
        "relative_module_import",
        "relative_module_shadow",
        "namespace_relative_module_import",
        "source_encodings",
        "typing",
        "typed_external_call",
        "typed_missing_member",
        "annotation_only_internal_receiver",
        "local_annotation_import_versions",
        "annotated_export_imports",
        "annotation_export_metadata",
        "annotation_import_boundary",
        "annotation_target_retention",
        "conditional_class_deletion_exports",
        "super_constructor_boundary",
        "typed_receiver_reassignment",
        "qualified_imported_call",
        "qualified_imported_receiver_rebinding",
        "missing_imported_scope",
        "absolute_imports",
        "shadowed_imports",
        "class_calls",
        "imported_value",
        "ignored_sources",
        "source_selection",
        "single_alias_fallback",
        "ambiguous_alias_fallback",
        "missing_imported_symbol",
        "lexical_imports",
        "reassigned_import",
        "relative_initializer_bases",
        "dotted_imports",
        "src_layout",
        "captured_import_call_argument",
        "imported_constructor_capture",
        "imported_inherited_constructor",
        "qualified_base_initializers",
        "imported_data_values",
        "conditional_import_targets",
        "conditional_reexport_chain",
        "import_occurrence_mapping",
        "imported_callable_aliases",
        "imported_callee_paths",
        "deterministic_import_targets",
        "exported_class_aliases",
        "constructor_receiver_identity",
        "annotated_member_constructors",
        "argument_constructor_inference",
        "star_imports",
        "static_all_exports",
        "export_detection",
        "nested_star_imports",
        "reexported_all",
        "reexported_without_all",
        "nested_imported_attribute_reads",
        "star_import_deletions",
        "static_all_annotated_binding",
        "static_all_multigen_comprehension",
        "static_all_unrelated_match_capture",
        "class_global_with_deletion",
        "initialized_module_annotation",
        "nested_attribute_walk",
        "module_receiver_annotation",
        "nested_package_module_read",
        "module_alias_attribute_target",
        "dynamic_call_resolution",
        "conditional_class_value_export",
        "coverage_routes",
        "coverage_submodule_fallback",
        "coverage_nested_callable",
        "coverage_external_base",
    ),
)
def test_package_fixture_snapshots(case: str):
    prefix = f"package/{case}"
    assert_fixture_sources_compile(FIXTURES_ROOT / prefix)

    source = {
        'source_selection': 'src',
        'src_layout': 'src/src_layout',
        'relative_module_import': 'regular',
    }.get(case, '.')
    scopes = build_package(FIXTURES_ROOT / prefix, package_name=case, source=source)

    assert to_dot(scopes) == read_fixture(f"{prefix}/expected_output.dot")
    document = json.loads(to_json(scopes))
    assert document == json.loads(read_fixture(f"{prefix}/expected_output.graph.json"))
    assert_graph_integrity(document)
    assert summarize(scopes) == json.loads(
        read_fixture(f"{prefix}/expected_output.summary.json")
    )


@pytest.mark.parametrize("case", ("module_name_collision", "source_file_symlink"))
def test_package_rejects_invalid_source_layout(case):
    prefix = f"package/{case}"
    assert_fixture_sources_compile(FIXTURES_ROOT / prefix)

    with pytest.raises(ValueError) as error:
        build_package(FIXTURES_ROOT / prefix, package_name="demo")

    assert str(error.value) == read_fixture(f"{prefix}/expected_output.error.txt").strip()


@pytest.mark.parametrize("analyze", (build_target, profile))
def test_single_file_entry_points_reject_source_file_symlink(analyze, monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)
    prefix = "package/source_file_symlink"

    with pytest.raises(ValueError) as error:
        analyze(f"{prefix}/alias.py")

    assert str(error.value) == read_fixture(f"{prefix}/expected_output.error.txt").strip()


def test_build_target_honors_source_encodings():
    fixture_root = FIXTURES_ROOT / "package/source_encodings"
    for filename in ("latin1.py", "utf8_bom.py", "utf8.py"):
        scopes = build_target(fixture_root / filename)
        assert scopes.children

    with pytest.raises(SyntaxError, match="invalid or missing encoding declaration"):
        build_target(fixture_root / "invalid_source.bytes")


def test_package_rejects_source_file_symlink_outside_source(tmp_path):
    package = tmp_path / "package"
    source = package / "src"
    package.mkdir()
    source.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("value = 1\n")
    (source / "linked.py").symlink_to(outside)

    with pytest.raises(ValueError, match="source file must be inside"):
        build_package(package, source="src")


def test_package_skips_ignored_files_before_resolving_symlinks(tmp_path):
    package = tmp_path / "package"
    ignored = package / ".venv"
    ignored.mkdir(parents=True)
    (package / "entry.py").write_text(read_fixture("package/ignored_sources/entry.py"))
    outside = tmp_path / "outside.py"
    outside.write_text("invalid syntax (\n")
    (ignored / "linked.py").symlink_to(outside)

    graph = build_package(package, package_name="ignored_sources")

    assert json.loads(to_json(graph)) == json.loads(
        read_fixture("package/ignored_sources/expected_output.graph.json")
    )


def test_package_does_not_recurse_into_symlinked_directories(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "entry.py").write_text(read_fixture("package/ignored_sources/entry.py"))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "invalid.py").write_text("invalid syntax (\n")
    (package / "linked").symlink_to(outside, target_is_directory=True)

    graph = build_package(package, package_name="ignored_sources")

    assert json.loads(to_json(graph)) == json.loads(
        read_fixture("package/ignored_sources/expected_output.graph.json")
    )


def test_package_rejects_source_outside_package_root(tmp_path):
    package = tmp_path / "package"
    package.mkdir()

    with pytest.raises(ValueError, match="source must be inside package root"):
        build_package(package, source="../outside")


def test_package_rejects_missing_source_directory(tmp_path):
    package = tmp_path / "package"
    package.mkdir()

    with pytest.raises(ValueError, match="source directory does not exist"):
        build_package(package, source="missing")


@pytest.mark.parametrize(
    ("builder", "target"),
    ((build_package, "."), (build_target, "."), (build_target, "nested/broken.py")),
)
def test_source_syntax_error_fixture(builder, target):
    fixture = FIXTURES_ROOT / "package/invalid_syntax"
    with pytest.raises(SyntaxError) as error:
        builder(fixture / target)

    failure = error.value
    assert {
        "exception": type(failure).__name__,
        "filename": Path(failure.filename).relative_to(fixture).as_posix(),
        "lineno": failure.lineno,
        "offset": failure.offset,
        "end_lineno": failure.end_lineno,
        "end_offset": failure.end_offset,
        "text": failure.text,
        "msg": failure.msg,
    } == json.loads(read_fixture("package/invalid_syntax/expected_output.error.json"))


@pytest.mark.parametrize("target", (".", "input.py"))
def test_deep_expression_error_fixture(target):
    fixture = FIXTURES_ROOT / "package/deep_expression_error"
    assert_fixture_sources_compile(fixture)
    previous_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(200)
        with pytest.raises(RecursionError) as error:
            build_target(fixture / target)
    finally:
        sys.setrecursionlimit(previous_limit)

    assert {"exception": type(error.value).__name__} == json.loads(
        read_fixture("package/deep_expression_error/expected_output.error.json")
    )
