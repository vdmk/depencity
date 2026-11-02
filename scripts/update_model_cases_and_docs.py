"""Regenerate documentation graphs and the refactoring comparison table."""

import subprocess
from pathlib import Path

import click

from depencity import build_target, summarize, to_dot


@click.command()
@click.option('--check', is_flag=True, help='Check generated outputs without modifying files.')
def main(check: bool) -> None:
    docs = Path(__file__).resolve().parents[1] / 'docs'
    updated = []
    for source in sorted([
        *docs.glob('cases-examples/*.py'),
        *docs.glob('refactoring-examples/*.py'),
    ]):
        dot = to_dot(build_target(source)) + '\n'
        svg = subprocess.run(
            ['dot', '-Tsvg'], input=dot, text=True,
            capture_output=True, check=True,
        ).stdout
        path = source.with_suffix('.svg')
        if path.exists() and path.read_text() == svg:
            continue
        if not check:
            path.write_text(svg)
        updated.append(path)
    path = docs / 'refactoring.md'
    document = _build_refactoring_document(path)
    if document != path.read_text():
        if not check:
            path.write_text(document)
        updated.append(path)
    for path in updated:
        print(path.relative_to(docs))
    if check:
        print(f'{len(updated)} stale artifact(s).')
        if updated:
            raise SystemExit(1)
    else:
        print(f'Updated {len(updated)} artifact(s).')


def _build_refactoring_document(path: Path) -> str:
    document = path.read_text()
    start = '<!-- refactoring-table:start -->'
    end = '<!-- refactoring-table:end -->'
    if document.count(start) != 1 or document.count(end) != 1:
        raise ValueError(f'{path}: expected one pair of refactoring table markers')
    before, remainder = document.split(start)
    _, after = remainder.split(end)
    profiles = []
    counts = []
    for version in ('before', 'after'):
        source = path.parent / 'refactoring-examples' / f'refactoring-{version}.py'
        summary = summarize(build_target(source), depth=2, include_own_profile=True)
        profiles.append(summary['scopes'][0]['profile'])
        counts.append(summary['scope_counts']['total'])
    rows = [
        '| Measurement | Before | After |',
        '| --- | ---: | ---: |',
        f'| Total scopes (root, module, function) | {counts[0]} | {counts[1]} |',
    ]
    for label, key in (
        ('Variable reads', 'variable.total.read.count'),
        ('Variable writes', 'variable.total.write.count'),
        ('Expression path count', 'graph.paths.expressions.count'),
        ('Maximum expression path length', 'graph.paths.expressions.length.max'),
        ('Data path count sum', 'graph.paths.data.count_sum'),
        ('Maximum data path length', 'graph.paths.data.length.max'),
        ('Mean data path length', 'graph.paths.data.length.mean'),
        ('Data path length p95', 'graph.paths.data.length.p95'),
        ('Version merges', 'graph.version_merges.count'),
        ('Cyclic components', 'graph.cyclic_components.count'),
    ):
        rows.append(f'| {label} | {profiles[0][key]} | {profiles[1][key]} |')
    return before + start + '\n' + '\n'.join(rows) + '\n' + end + after


if __name__ == '__main__':
    main()
