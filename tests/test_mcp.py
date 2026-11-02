import pytest

from depencity.mcp import _resolve_workspace_path


def test_inside_rejects_paths_outside_workspace(tmp_path):
    with pytest.raises(ValueError):
        _resolve_workspace_path(tmp_path, tmp_path.parent / 'outside.py')


def test_inside_uses_root_when_value_is_missing(tmp_path):
    assert _resolve_workspace_path(tmp_path, None) == tmp_path
