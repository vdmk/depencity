# Integration Test Guidelines

Keep integration tests aligned with the public module they exercise. Keep the
fixture layout shallow: `fixtures/builder/` belongs to
`depencity._graph.graph_builder`, and `fixtures/package/` belongs to
`depencity._package_graph.package_builder`. Each case gets one directory below its
target directory, such as `builder/language_surface/` or
`package/internal_calls/`. Do not use the integration test filename as the
fixture prefix.

Author each source fixture as a normal `.py` file. No fixture files are created
or modified at runtime.

Structure each test as Arrange, Act, Assert. Call a public high-level entry
point such as `build_target` or `build_package`, and ensure every fixture exposes a
clear `main` entry function when that is the scenario under test. Store three
independent deterministic artifacts for every case: DOT, graph JSON, and a
compact summary JSON. Snapshot names follow
`input.py` for single-file source and
`<case>.expected_output.<artifact>.<extension>` for each expected artifact;
the analyzed entry point is always `main` and is not repeated in filenames.
Multi-file source fixtures use honest module filenames directly under the case
directory, such as `package/internal_calls/entry.py`; pass the logical package
name separately.

Keep syntax and data-flow coverage in these integration snapshots. Unit tests
are discouraged, but appropriate for local branching that public snapshots
cannot isolate or algorithms with many edge cases. Keep unit tests small.
Before adding a unit test, check whether
an existing fixture snapshot already covers the behavior; do not add a
duplicate unit test when the snapshot already exercises and asserts that case.
Do not add fixture-specific assertions to a shared snapshot test for behavior
already captured by its DOT, graph JSON, and summary snapshots. Add custom
assertions only for invariants those artifacts cannot express.

For MCP integration behavior, represent each request shape as a JSON fixture.
Keep the source under `fixtures/builder/<case>/input.py`, call the public MCP
`profile` entry point in the test, and compare the complete JSON response with
`expected_output.<detail>.<case>.json`. Put request parameters such as `scope`,
navigation flags, and `metrics` in the test's parameter table rather than
asserting selected fields inline. Regenerate snapshots deliberately when the
public response contract changes.
