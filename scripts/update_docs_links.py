"""Update documentation references to match the package version."""

import re
import runpy
import tomllib
from pathlib import Path

import click


@click.command()
@click.option('--check', is_flag=True, help='Check generated outputs without modifying files.')
def main(check: bool) -> None:
    root = Path(__file__).resolve().parents[1]
    version = runpy.run_path(root / 'src/depencity/_version.py')['__version__']
    readme_path = root / 'README.md'
    readme = readme_path.read_text()
    metadata_path = root / 'pyproject.toml'
    metadata_text = metadata_path.read_text()
    metadata = tomllib.loads(metadata_text)
    documentation = metadata['project']['urls']['Documentation']
    errors = []
    expected = f'https://github.com/vdmk/depencity/blob/v{version}/README.md'
    link_pattern = re.compile(
        r'(https://(?:github\.com/vdmk/depencity/(?:blob|tree)/'
        r'|raw\.githubusercontent\.com/vdmk/depencity/))([^/\s)<>]+)(/[^\s)<>]+)',
    )
    if not check:
        updated_readme = link_pattern.sub(
            lambda match: f'{match[1]}v{version}{match[3]}', readme,
        )
        if updated_readme != readme:
            readme_path.write_text(updated_readme)
            readme = updated_readme
        if documentation != expected:
            metadata_path.write_text(metadata_text.replace(documentation, expected))
            documentation = expected

    if documentation != expected:
        errors.append(f'pyproject.toml: expected Documentation = {expected}')

    links = list(link_pattern.finditer(readme))
    if not links:
        errors.append('README.md: no repository documentation links found')
    for link in links:
        if link[2] != f'v{version}':
            errors.append(f'README.md: expected tag v{version} in {link[0]}')

    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Documentation links match package version {version}.')


if __name__ == '__main__':
    main()
