"""Refresh complete graph and summary snapshots for builder and package fixtures."""

import json
from pathlib import Path
from unittest.mock import patch

import click
from click.testing import CliRunner

from depencity import build_package, build_target, cli, summarize, to_dot, to_json
from depencity._profile.summary import summarize_document


@click.command()
@click.option('--check', is_flag=True, help='Check generated outputs without modifying files.')
def main(check: bool) -> None:
    repository = Path(__file__).resolve().parents[1]
    fixtures = repository / 'tests' / 'fixtures'
    updated = []
    for category in ('builder', 'package'):
        for case in sorted((fixtures / category).iterdir()):
            graph_path = case / 'expected_output.graph.json'
            if not graph_path.exists():
                continue
            scopes = _build_fixture(category, case)
            if _write_snapshot(graph_path, to_json(scopes), check):
                updated.append(graph_path)
            dot_path = case / 'expected_output.dot'
            if _write_snapshot(dot_path, to_dot(scopes), check):
                updated.append(dot_path)
            summary_path = case / 'expected_output.summary.json'
            if summary_path.exists():
                output = json.dumps(
                    summarize(scopes),
                    indent=2, sort_keys=True,
                )
                if _write_snapshot(summary_path, output, check):
                    updated.append(summary_path)

    for path, output in _build_scoped_profile_snapshots(fixtures / 'builder'):
        if _write_snapshot(path, output, check):
            updated.append(path)

    for case in sorted((fixtures / 'summary').iterdir()):
        document = json.loads((case / 'input.json').read_text())
        path = case / 'expected_output.summary.json'
        output = json.dumps(summarize_document(document), indent=2, sort_keys=True)
        if _write_snapshot(path, output, check):
            updated.append(path)
        if case.name == 'edge_cases':
            path = case / 'expected_output.filtered.summary.json'
            output = json.dumps(
                summarize_document(
                    document, metrics=['graph.paths.expressions.count']
                ),
                indent=2,
                sort_keys=True,
            )
            if _write_snapshot(path, output, check):
                updated.append(path)

    for target, prefix in (
        (fixtures / 'package' / 'internal_calls', 'profile'),
        (fixtures / 'builder' / 'path_count_limit' / 'input.py', 'profile_path_count_limit'),
    ):
        for suffix in ('aggregate', 'own'):
            arguments = [
                'profile', str(target), '--format', 'text', '--depth', '1',
            ]
            if suffix == 'own':
                arguments.append('--include-own-profile')
            result = CliRunner().invoke(cli.main, arguments)
            if result.exit_code:
                raise RuntimeError(result.output) from result.exception
            path = fixtures / 'cli' / f'{prefix}_{suffix}.txt'
            if _write_snapshot(path, result.output, check):
                updated.append(path)

    for path in updated:
        print(path.relative_to(repository))
    if check:
        print(f'{len(updated)} stale snapshot(s).')
        if updated:
            raise SystemExit(1)
    else:
        print(f'Updated {len(updated)} snapshot(s).')


def _build_fixture(category: str, case: Path):
    if category == 'builder':
        source = case / 'input.py'
        if source.exists():
            return build_target(source)
        raise FileNotFoundError(f'No builder input found: {source}')

    source = {
        'source_selection': 'src',
        'src_layout': 'src/src_layout',
        'relative_module_import': 'regular',
    }.get(case.name, '.')
    return build_package(case, package_name=case.name, source=source)


def _build_scoped_profile_snapshots(fixtures: Path):
    navigation_case = fixtures / 'scope_navigation'
    navigation_graph = _build_fixture('builder', navigation_case)
    function_id = next(
        scope.path()
        for scope in navigation_graph.walk_scopes()
        if scope.kind == 'function'
    )
    options = {
        'exact': (False, False),
        'children': (True, False),
        'parent': (False, True),
        'navigation': (True, True),
    }
    for name, (include_children, include_parent) in options.items():
        result = summarize(
            navigation_graph,
            scope_id=function_id,
            include_children=include_children,
            include_parent=include_parent,
        )
        yield (
            navigation_case / f'expected_output.{name}.json',
            json.dumps(result, indent=2, sort_keys=True),
        )

    for filename, result in (
        (
            'expected_output.depth_zero.json',
            summarize(navigation_graph, depth=0),
        ),
        (
            'expected_output.depth_one.json',
            summarize(navigation_graph, depth=1),
        ),
        (
            'expected_output.own_profile.json',
            summarize(navigation_graph, include_own_profile=True),
        ),
        (
            'expected_output.metrics.json',
            summarize(
                navigation_graph,
                include_own_profile=True,
                metrics=['call.occurrences.total.count'],
            ),
        ),
        (
            'expected_output.empty_metrics.json',
            summarize(navigation_graph, include_own_profile=True, metrics=[]),
        ),
    ):
        yield navigation_case / filename, json.dumps(result, indent=2, sort_keys=True)

    metric_case = fixtures / 'metric_filter'
    metric_graph = _build_fixture('builder', metric_case)
    result = summarize(
        metric_graph,
        scope_id='outer',
        include_children=True,
        include_parent=True,
        metrics=['graph.paths.expressions.count'],
    )
    yield (
        metric_case / 'expected_output.navigation.json',
        json.dumps(result, indent=2, sort_keys=True),
    )


def _write_snapshot(path: Path, output: str, check: bool) -> bool:
    if path.exists() and path.read_text() == output:
        return False
    if not check:
        path.write_text(output)
    return True


if __name__ == '__main__':
    with (
        patch("depencity._graph.export.json.version", return_value="0.0.0"),
        patch("depencity._profile.summary.version", return_value="0.0.0"),
    ):
        main()
