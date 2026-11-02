import json

import pytest
from click.testing import CliRunner

from depencity import __version__, build_target, cli, summarize
from depencity.mcp import profile

from .utils import FIXTURES_ROOT, read_fixture


def test_cli_reports_version():
    result = CliRunner().invoke(cli.main, ['--version'])

    assert result.exit_code == 0
    assert result.output == f'depencity, version {__version__}\n'


@pytest.mark.parametrize("output_format", ('dot', 'json'))
def test_cli_graph_export_matches_fixture(output_format: str):
    path = FIXTURES_ROOT / "builder" / "resolver_cases" / "input.py"

    result = CliRunner().invoke(cli.main, [
        'graph', str(path), '--format', output_format,
    ])

    assert result.exit_code == 0
    output = result.output.rstrip("\n")
    expected_name = "expected_output.dot" if output_format == 'dot' else "expected_output.graph.json"
    expected = read_fixture(f"builder/resolver_cases/{expected_name}")
    if output_format == 'json':
        assert json.loads(output) == json.loads(expected)
    else:
        assert output == expected


def test_cli_exports_package_graph():
    root = FIXTURES_ROOT / 'package' / 'internal_calls'

    result = CliRunner().invoke(cli.main, [
        'graph', str(root), '--format', 'json',
    ])

    assert result.exit_code == 0
    output = result.output
    expected = read_fixture('package/internal_calls/expected_output.graph.json')
    assert json.loads(output) == json.loads(expected)


@pytest.mark.parametrize('target', (
    'builder/resolver_cases/input.py',
    'package/internal_calls',
))
@pytest.mark.parametrize('depth,include_own_profile', ((None, False), (0, True), (2, True)))
def test_cli_profile_json_matches_summary(target, depth, include_own_profile, monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)
    path = FIXTURES_ROOT / target
    arguments = ['profile', str(path), '--format', 'json']
    if depth is not None:
        arguments.extend(['--depth', str(depth)])
    if include_own_profile:
        arguments.append('--include-own-profile')
    expected = summarize(
        build_target(path), depth=depth, include_own_profile=include_own_profile,
    )

    result = CliRunner().invoke(cli.main, arguments)

    assert result.exit_code == 0
    assert json.loads(result.output) == expected
    assert result.output == profile(
        str(path), depth=depth, include_own_profile=include_own_profile,
    ) + '\n'


def test_cli_profile_maps_options_to_summary(monkeypatch):
    calls = []

    def profile(root, **options):
        calls.append(options)
        return {'scope_counts': {'total': 0}, 'scopes': []}

    monkeypatch.setattr(cli, 'summarize', profile)
    monkeypatch.setattr(cli, 'build_target', lambda path, source: None)
    result = CliRunner().invoke(cli.main, [
        'profile', 'src', '--source', 'package',
        '--include-own-profile',
    ])

    assert result.exit_code == 0
    assert calls == [{
        'depth': None,
        'include_own_profile': True,
    }]
    assert result.output == 'Scopes: 0 total\n'


def test_cli_without_command_reports_usage():
    result = CliRunner().invoke(cli.main)

    assert result.exit_code == 2
    assert 'Usage: depencity' in result.output


@pytest.mark.parametrize('include_own_profile', (False, True))
def test_cli_profile_text_matches_fixture(include_own_profile):
    path = FIXTURES_ROOT / 'package' / 'internal_calls'
    arguments = ['profile', str(path), '--format', 'text', '--depth', '1']
    if include_own_profile:
        arguments.append('--include-own-profile')

    result = CliRunner().invoke(cli.main, arguments)

    assert result.exit_code == 0
    suffix = 'own' if include_own_profile else 'aggregate'
    assert result.output == read_fixture(f'cli/profile_{suffix}.txt')
