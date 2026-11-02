import asyncio
import json

import pytest
from click.testing import CliRunner

import depencity.mcp as mcp_module
from depencity.mcp import create_server, profile

from .utils import FIXTURES_ROOT, read_fixture


def test_mcp_profile_matches_fixture_summary(monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)

    result = json.loads(
        profile("builder/resolver_cases/input.py")
    )

    expected = json.loads(
        read_fixture("builder/resolver_cases/expected_output.summary.json")
    )
    assert result == expected
    assert "own_profile" not in result["scopes"][0]


def test_mcp_profile_matches_package_fixture_summary(monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)

    result = json.loads(profile("package/internal_calls"))
    expected = json.loads(
        read_fixture("package/internal_calls/expected_output.summary.json")
    )

    assert result == expected


def test_mcp_profile_accepts_selected_package_sources(monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)

    result = json.loads(
        profile("package/source_selection", source="src")
    )
    expected = json.loads(
        read_fixture("package/source_selection/expected_output.summary.json")
    )

    assert result == expected


def test_mcp_profile_accepts_relative_and_absolute_paths(monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)
    relative = json.loads(
        profile("builder/resolver_cases/input.py", workspace=".")
    )
    absolute_path = FIXTURES_ROOT / "builder/resolver_cases/input.py"
    absolute = json.loads(
        profile(str(absolute_path), workspace=str(FIXTURES_ROOT))
    )

    assert absolute == relative


def test_mcp_profile_metric_filter_matches_fixture(monkeypatch):
    monkeypatch.chdir(FIXTURES_ROOT)
    result = json.loads(
        profile(
            "builder/metric_filter/input.py",
            scope='outer',
            include_children=True,
            include_parent=True,
            metrics=['graph.paths.expressions.count'],
        )
    )
    expected = json.loads(
        read_fixture('builder/metric_filter/expected_output.navigation.json')
    )
    assert result == expected


@pytest.mark.parametrize(
    ('options', 'message'),
    (
        ({'scope': 'missing'}, 'unknown scope: missing'),
        ({'depth': -1}, 'depth must be'),
        ({'depth': 1.5}, 'depth must be'),
        ({'depth': True}, 'depth must be'),
    ),
)
def test_mcp_profile_rejects_invalid_selection(monkeypatch, options, message):
    monkeypatch.chdir(FIXTURES_ROOT)

    with pytest.raises(ValueError, match=message):
        profile('builder/resolver_cases/input.py', **options)


@pytest.mark.parametrize(
    ('case', 'include_children', 'include_parent'),
    (
        ('exact', False, False),
        ('children', True, False),
        ('parent', False, True),
        ('navigation', True, True),
    ),
)
def test_mcp_profile_scope_navigation_options(
    monkeypatch, case, include_children, include_parent
):
    monkeypatch.chdir(FIXTURES_ROOT)

    overview = json.loads(profile("builder/scope_navigation/input.py"))
    selected_scope = next(
        item
        for item in overview['scopes'][0]['children'][0]['children']
        if item['kind'] == 'function'
    )
    result = json.loads(
        profile(
            "builder/scope_navigation/input.py",
            scope=selected_scope['id'],
            include_children=include_children,
            include_parent=include_parent,
        )
    )
    expected = json.loads(
        read_fixture(
            f"builder/scope_navigation/expected_output.{case}.json"
        )
    )
    assert result == expected


@pytest.mark.parametrize(
    ('filename', 'depth', 'include_own_profile', 'metrics'),
    (
        ('expected_output.depth_zero.json', 0, False, None),
        ('expected_output.depth_one.json', 1, False, None),
        ('expected_output.own_profile.json', None, True, None),
        ('expected_output.metrics.json', None, True, ['call.occurrences.total.count']),
        ('expected_output.empty_metrics.json', None, True, []),
    ),
)
def test_mcp_profile_options_match_fixture(
    monkeypatch, filename, depth, include_own_profile, metrics
):
    monkeypatch.chdir(FIXTURES_ROOT)

    result = json.loads(profile(
        'builder/scope_navigation/input.py', depth=depth,
        include_own_profile=include_own_profile,
        metrics=metrics,
    ))

    assert result == json.loads(read_fixture(f'builder/scope_navigation/{filename}'))


def test_graph_mcp_exposes_only_graph_tools():
    tools = asyncio.run(create_server().list_tools())

    assert {tool.name for tool in tools} == {"profile"}


def test_mcp_cli_starts_server_in_workspace(tmp_path, monkeypatch):
    calls = []

    class FakeServer:
        def run(self):
            calls.append('run')

    monkeypatch.setattr(mcp_module, 'create_server', lambda: FakeServer())
    result = CliRunner().invoke(mcp_module.main, ['--workspace', str(tmp_path)])

    assert result.exit_code == 0
    assert calls == ['run']
