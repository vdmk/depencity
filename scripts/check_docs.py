"""Check local documentation links, heading anchors, and CLI/MCP examples."""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin

from depencity.mcp import profile


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = []
    pages = [*root.glob('*.md'), *(root / 'docs').glob('*.md')]
    parser = MarkdownIt('commonmark').enable('table').use(anchors_plugin, max_level=6)
    for page in pages:
        _, links = _parse_document(parser, page)
        for target in links:
            link = urlsplit(target)
            if link.scheme or link.netloc:
                continue
            destination = page.parent / unquote(link.path) if link.path else page
            if not destination.exists():
                errors.append(f'{page.relative_to(root)}: missing target {target}')
            elif link.fragment and destination.suffix == '.md':
                anchors, _ = _parse_document(parser, destination)
                if unquote(link.fragment) not in anchors:
                    errors.append(f'{page.relative_to(root)}: missing heading {target}')

    source = root / 'docs/cases-examples/readme-example.py'
    result = subprocess.run(
        [sys.executable, '-c', 'from depencity.cli import main; main()',
         'profile', str(source),
         '--depth', '2', '--include-own-profile', '--format', 'json'],
        capture_output=True, text=True, check=True,
    )
    summary = json.loads(result.stdout)
    if summary['scope_counts']['total'] != 3:
        errors.append('CLI example: expected root, module, and function scopes')
    selected = json.loads(profile(
        str(source), depth=2,
        metrics=['variable.total.read.count', 'graph.cyclic_components.count'],
    ))
    if selected['scopes'][0]['profile'] != {
        'variable.total.read.count': 4, 'graph.cyclic_components.count': 0,
    }:
        errors.append('MCP example: unexpected selected measurements')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Checked local file links and heading anchors in {len(pages)} pages and CLI/MCP examples.')


def _parse_document(parser: MarkdownIt, page: Path) -> tuple[set[str], list[str]]:
    anchors = set()
    links = []
    pending = list(parser.parse(page.read_text()))
    while pending:
        token = pending.pop()
        if token.type == 'heading_open':
            anchors.add(token.attrGet('id'))
        elif token.type == 'link_open':
            links.append(token.attrGet('href'))
        elif token.type == 'image':
            links.append(token.attrGet('src'))
        pending.extend(token.children or [])
    return anchors, links


if __name__ == '__main__':
    main()
