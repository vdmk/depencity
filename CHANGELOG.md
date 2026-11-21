# Changelog

## 0.1.1

- Add SLSA build provenance and PyPI publish attestations for the wheel and source distribution.

## 0.1.0

Initial experimental release.

- Static dependency graphs for Python files and packages, exported as JSON or DOT.
- Scope profiles for reads, writes, calls, containers, dependency paths, and cycles.
- Python API, CLI with text/JSON profiles, and a workspace-scoped MCP server.
- Analyzer version included in graph JSON and profile summaries.

The graph model and output formats are experimental. Private names retain their
source spelling; Python name mangling is not connected.
