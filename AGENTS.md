# Depencity Guidelines

## Coding and API Boundaries

Name functions with a verb describing their action; `main` is the exception.
Within classes, place callers before the methods they call.

The top-level `src/depencity/__init__.py` defines the public Python API through
explicit re-exports and `__all__`. Keep internal package initializers code-free.
Implementation modules import definitions directly rather than through the
top-level initializer. Underscore-prefixed packages, including the IR and
resolution machinery, are internal and may change in patch releases.

Use `uv run` for non-trivial Python scripts.

## Refactoring and Module Placement

Place operations beside the data and context they own. Package discovery belongs
with package orchestration; resolution between existing scopes belongs with
resolution. A shared verb or shorter file is not sufficient reason to move code.
Avoid generic helpers that merely relocate complexity or deepen call chains.

Preserve public behavior, dependency meaning, edge direction, and metric names.
Treat deliberate model changes separately from implementation refactoring.
Use compact before/after profiles for refactoring; request extended output only
for a specific hotspot. Compare affected scopes, scope counts, path counts and
lengths, and cycles alongside the source. Smaller counters alone are not enough.
Prefer clear finite `if`/`elif` branches over temporary lookup tables introduced
only to reduce a metric. Do not replace a generator with `map` just to remove a
comprehension scope; the new external dependency is not a net simplification.

## Keep the POC Lightweight

Do not add unnecessary ceremony. Avoid migration layers, compatibility wrappers,
process abstractions, or other production
machinery unless the current POC demonstrably needs it.

Prefer fewer module, class, and function scopes. A new scope must be justified
by removing existing graph complexity or concepts, not by merely moving the
same nodes and edges to another level. Count real scopes as entities;
aggregations are reporting summaries, not new entities.

## Language-Agnostic Dependency Model

Treat modeled dependencies uniformly as data items. Omit an import only when
the dependency model determines that it is unused.

Type annotations are metadata for member resolution, not data dependencies.
Do not add them to the graph; imports used only in annotations may be omitted.

Do not create synthetic deletion nodes for implicit scope clearings, such as
Python clearing an exception alias after its handler. The graph models operations
written in source code; represent the resulting visibility by rewiring which
binding nodes later reads can depend on.

## Analysis Boundaries

Use [analysis boundaries](docs/analysis-boundaries.md) when reviewing
analyzer bugs and feature requests.

- Fix incorrect dependencies within supported behavior.
- Accept documented approximations; do not classify them as bugs merely because
  Python can behave differently at runtime.
- Reject proposed extensions beyond these boundaries unless a concrete benefit
  justifies expanding the model. Do not add runtime evaluation or special cases
  solely to reproduce more Python behavior.
- When intentionally changing a boundary, update its documentation and fixture
  coverage together.

## Validation and Fixture Snapshots

Follow [the testing guidelines](tests/AGENTS.md), the source of truth for test
policy. Use fixture snapshots for analyzer behavior, extending coverage for
previously untested cases. Small unit tests may cover local branching or
algorithmic edge cases that public snapshots cannot isolate; do not duplicate
existing snapshot coverage.
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, linting, tests,
and the snapshot-update command. Commands there run from this package's
root, which becomes the repository root after extraction.

Whenever analyzer behavior or builder/package fixture sources change, regenerate
complete DOT, graph JSON, and summary snapshots with the repository script.
Do not patch individual metrics or regenerate snapshots with ad hoc scripts.
Preserve each summary's detail level, review the diff, and rerun the script to
confirm zero updates before accepting snapshots.

When analyzer behavior or documentation example sources change, also regenerate
the model-case graphs using the command in CONTRIBUTING.md and review the diff.

## Measuring Source

```bash
uv run depencity profile src/depencity/_graph/graph_builder.py
uv run depencity graph path/to/file.py --format dot
```

Treat profiles as directional evidence, not universal quality scores. Do not
remove a useful naming alias such as `all_nodes = scope.nodes` solely for an
incidental counter reduction; readability and actual dependencies matter.

## Release

1. Run `uv version <version>` to bump the version in `pyproject.toml`, then run
   `uv run scripts/update_docs_links.py` to update documentation links.
   Update `CHANGELOG.md` under the release version.
2. Run the development, test, and distribution checks in `CONTRIBUTING.md`.
   Run `uv run --locked scripts/check_security.py` again after the final commit.
   Ensure `dist/` contains only the new version's wheel and sdist.
3. Push to `main`. Actions validates and tags the release, then publishes the
   tested `Packages` artifact through Trusted Publishing. Existing tags remain
   unchanged; only the commit targeted by the version tag can publish.
   Retry interrupted publication by rerunning failed jobs in the original run,
   preserving its tested artifact. Do not rebuild or move the tag to retry.
4. Wait for publication and installation verification to pass.
   Inspect the PyPI page rendering and links after publication. Use a new
   version for any correction to a published release.
