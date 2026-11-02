from pathlib import Path

import click

from depencity._graph.export.dot import to_dot
from depencity._graph.export.json import to_json
from depencity._package_graph.package_builder import build_target
from depencity._profile.summary import serialize_summary, summarize
from depencity._version import __version__


@click.group(name='depencity')
@click.version_option(version=__version__, prog_name='depencity')
def main() -> None:
    """Analyze code through the local complexity tools."""


@main.command(name='profile')
@click.argument('path', type=click.Path(path_type=Path))
@click.option('--format', 'output_format', type=click.Choice(('text', 'json')), default='text', show_default=True, help='Profile output format')
@click.option('--source', default='.', show_default=True, help='Package source directory relative to path; module names are prefixed by the target directory name')
@click.option('--depth', type=click.IntRange(min=0), default=None, help='Scope tree depth (default: full tree; 0: roots only)')
@click.option('--include-own-profile', is_flag=True, help='Include metrics for each scope without its descendants')
def run_profile(path: Path, output_format: str, source: str, depth: int | None, include_own_profile: bool) -> None:
    try:
        result = summarize(
            build_target(path, source),
            depth=depth,
            include_own_profile=include_own_profile,
        )
    except (OSError, SyntaxError, ValueError, NotImplementedError) as error:
        raise click.ClickException(str(error)) from error
    if output_format == 'json':
        click.echo(serialize_summary(result))
    else:
        _print_profile(result)


@main.command(name='graph')
@click.argument('path', type=click.Path(path_type=Path))
@click.option('--format', 'output_format', type=click.Choice(('dot', 'json')), required=True)
@click.option('--source', default='.', show_default=True, help='Package source directory relative to path; module names are prefixed by the target directory name')
def export_graph(path: Path, output_format: str, source: str) -> None:
    try:
        root = build_target(path, source)
    except (OSError, SyntaxError, ValueError, NotImplementedError) as error:
        raise click.ClickException(str(error)) from error
    result = (
        to_dot(root)
        if output_format == 'dot'
        else to_json(root)
    )
    click.echo(result)


def _print_profile(result: dict) -> None:
    counts = result['scope_counts']
    click.echo('Scopes: ' + ', '.join(
        f'{value} {kind}' for kind, value in sorted(counts.items())
    ))
    for scope in result['scopes']:
        _print_scope(scope)


def _print_scope(scope: dict, depth: int = 0) -> None:
    indent = '  ' * depth
    click.echo(f"\n{indent}{scope['id']} [{scope['kind']}]")
    own = scope.get('own_profile')
    if own is not None:
        click.echo(f'{indent}  {"Metric":<{max(1, 48 - len(indent))}} {"Aggregate":>12} {"Own":>12}')
    metrics: dict[str, dict] = {}
    for key, value in scope['profile'].items():
        category, name = key.split('.', 1)
        metrics.setdefault(category, {})[name] = value
    _print_metrics(metrics, own, indent + '  ')
    for child in scope.get('children', []):
        _print_scope(child, depth + 1)


def _print_metrics(metrics: dict, own: dict | None,
                   indent: str, prefix: str = '') -> None:
    for name, value in metrics.items():
        key = f'{prefix}.{name}' if prefix else name
        label = str(name).replace('_', ' ').replace('.', ' ').capitalize()
        if key.endswith('.distribution'):
            click.echo(f'{indent}{label} (length: paths)')
            own_buckets = own[key] if own is not None else {}
            for bucket in sorted(value.keys() | own_buckets.keys(), key=int):
                row = f'{indent}  {bucket:<{max(1, 48 - len(indent))}} {value.get(bucket, 0):>12}'
                if own is not None:
                    row += f' {own_buckets.get(bucket, 0):>12}'
                click.echo(row)
        elif isinstance(value, dict):
            click.echo(f'{indent}{label}')
            _print_metrics(value, own, indent + '  ', key)
        else:
            displayed = f'{value:.6g}' if isinstance(value, float) else str(value)
            row = f'{indent}{label:<{max(1, 50 - len(indent))}} {displayed:>12}'
            if own is not None:
                own_value = own[key]
                displayed_own = f'{own_value:.6g}' if isinstance(own_value, float) else str(own_value)
                row += f' {displayed_own:>12}'
            click.echo(row)
