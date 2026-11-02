# Contributing

To report a bug, please open an issue with the Depencity version, a minimal
source example, the command or API call, and the expected and actual results.
The [analysis boundaries](docs/analysis-boundaries.md) can help clarify whether
behavior is supported. For feature proposals, please describe the use case and
benefit. PRs should explain the problem, the change, and how it was validated;
the checks below can help.

The [agent guidelines](AGENTS.md) cover the development conventions. A few
points to keep in mind:

- The [agent testing guidelines](tests/AGENTS.md) define the test policy. Fixture
  snapshots cover analyzer behavior; unit tests are discouraged, but appropriate for local
  branching that public snapshots cannot isolate or algorithms with many edge cases.
  Checking existing snapshots helps avoid duplicate coverage. The scripts below
  regenerate complete artifacts for review.
- Intentional changes to analysis boundaries need documentation and fixture
  coverage together.
- Refactoring should preserve public behavior, dependency meaning, edge
  direction, and metric names. Deliberate model changes belong in separate work.
- Public Python exports are defined in `src/depencity/__init__.py` and `__all__`.
  Internal package initializers stay code-free, and implementation modules
  import definitions directly from their modules.
- Function names use action verbs (`main` is the exception). Within classes,
  callers appear before the methods they call. Simple solutions suit this POC.

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Run the following commands from the checkout root:

```bash
uv sync --locked
uv run ruff check src tests scripts
uv run mypy
uv run scripts/check_docs.py
uv run scripts/update_docs_links.py --check
```

The documentation check verifies local file targets, Markdown heading anchors,
and canonical CLI/MCP profile examples. It does not fetch external URLs. Before
a release, check that versioned README links and the example image resolve
after the release tag is available.

Run the complete test suite with two pytest workers:

```bash
uv run pytest -q -n 2
```

The test suite checks fixture snapshots with two pytest workers. After changing
analyzer behavior or fixture sources, regenerate complete snapshots and review
the diff:

```bash
uv run scripts/update_fixture_profiles.py
```

Check snapshots without modifying files, then rerun tests:

```bash
uv run scripts/update_fixture_profiles.py --check
```

To regenerate documentation graphs and the refactoring comparison table from `docs/cases-examples/*.py` and
`docs/refactoring-examples/*.py`, install Docker and run from the checkout root:

```bash
docker build --platform linux/amd64 -f docker/docs/Dockerfile -t depencity-docs .
docker run --rm --platform linux/amd64 --network none --user "$(id -u):$(id -g)" -v "$PWD:/workspace" depencity-docs
```

This passes DOT directly to Graphviz and writes an SVG beside each source
example. It also regenerates the marked table in `docs/refactoring.md` from the
before/after sources. Missing table markers are an error. Review the diff and
check the surrounding explanation when measurements change, then verify without
modifying files:

```bash
docker run --rm --platform linux/amd64 --network none -v "$PWD:/workspace:ro" depencity-docs --check
```

Both generators report stale paths and exit with status 1 in check mode when
outputs differ. Without `--check`, they regenerate the outputs.

CI runs all three update scripts with `--check`, using the same Docker
environment for SVG comparison. Use the Docker commands above to match its
Graphviz, fonts, and architecture. Rebuild after dependency changes; when
changing the renderer in `docker/docs/Dockerfile`, regenerate and review all
SVGs together.

Update versioned README and package documentation links after a version bump:

```bash
uv run scripts/update_docs_links.py
```

Use `--check` to verify links without modifying them; mismatches exit nonzero.
This checks version consistency, not live URL availability.

## Security checks

CI runs source scanning and an audit of installed dependencies:

```bash
uv run --locked bandit -c pyproject.toml -r src
uv run --locked pip-audit --local --skip-editable
```

For the additional Git-history secret scan required by the release guidelines,
install `gitleaks` on PATH and run:

```bash
uv run --locked scripts/check_security.py
```

This runs Gitleaks, Bandit, and pip-audit. The dependency audit requires network
access to retrieve vulnerability information.

## Distribution checks

```bash
uv build
uvx twine check --strict dist/*
uvx --with tox-uv tox run --installpkg dist/*.whl
uvx --with tox-uv tox run --recreate --installpkg dist/*.tar.gz
```

CI checks distribution contents and metadata, then runs the existing suite
against installed wheel and sdist packages using tox.
