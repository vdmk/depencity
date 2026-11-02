"""MCP profiling within a configured workspace."""

from __future__ import annotations

import os
from pathlib import Path

import click
from mcp.server import MCPServer

from depencity._package_graph.package_builder import build_target
from depencity._profile.summary import serialize_summary, summarize


@click.command(name='depencity-mcp')
@click.option('--workspace', type=click.Path(path_type=Path, exists=True, file_okay=False), default='.', show_default=True)
def main(workspace: Path) -> None:
    workspace_root = workspace.resolve()
    try:
        os.chdir(workspace_root)
    except OSError as error:
        raise click.ClickException(str(error)) from error
    create_server().run()


def create_server():
    mcp = MCPServer('depencity')
    mcp.add_tool(profile)
    return mcp


def profile(
    path: str,
    workspace: str | None = None,
    source: str = '.',
    scope: str | None = None,
    include_children: bool = False,
    include_parent: bool = False,
    metrics: list[str] | None = None,
    depth: int | None = None,
    include_own_profile: bool = False,
) -> str:
    """Return a target's scope profiles as JSON.

    Args:
        path: File or directory inside the selected workspace.
        workspace: Directory inside the server workspace used to resolve path;
            defaults to the server workspace.
        source: Source directory relative to a directory target; ignored for files.
        scope: Exact scope ID; None selects all scopes.
        include_children: With scope, also select its immediate children.
        include_parent: With scope, also select its parent.
        metrics: Metric names to return; None includes all, [] omits metrics.
        depth: Display depth from selected roots; 0 shows roots, None the full tree.
        include_own_profile: Include metrics for each scope alone.

    Aggregate profiles include descendants beyond the displayed depth.
    """
    base = _resolve_workspace_path(Path.cwd().resolve(), workspace)
    target = _resolve_workspace_path(base, path)
    return serialize_summary(
        summarize(
            build_target(target, source),
            scope_id=scope,
            include_children=include_children,
            include_parent=include_parent,
            metrics=metrics,
            depth=depth,
            include_own_profile=include_own_profile,
        ),
    )


def _resolve_workspace_path(root: Path, value: str | Path | None) -> Path:
    root = root.resolve()
    path = root / Path(value or '.')
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'path must be inside workspace: {root}')
    return path
