# Python API

Depencity is mainly used through the CLI and MCP server, but also provides the
Python API documented here.

## Install

Requires Python 3.14+. Add the package to your Python project:

```bash
uv add depencity
```

## Build a graph

```python
from depencity import build_target, summarize, to_dot, to_json

graph = build_target("path/to/file.py")
summary = summarize(graph, depth=2, include_own_profile=True)
graph_json = to_json(graph)
graph_dot = to_dot(graph)
```

Each builder returns a root `Scope`. Source code is parsed without being executed.
Paths accept `str` or `pathlib.Path`; relative paths use the current directory.

| Function | Behavior |
| --- | --- |
| `build(source: str) -> Scope` | Analyze one module supplied as Python source text. |
| `build_target(path, source='.') -> Scope` | Analyze a file or directory. `source` selects a directory relative to a directory target; it is ignored for a file. |
| `build_package(root, package_name=None, source='.') -> Scope` | Discover modules beneath `root / source` and connect internal imports. The source directory must stay inside `root`. Module names are prefixed by `package_name`, defaulting to `root`'s directory name. |

For a package with sources in `src/my_package`:

```python
from depencity import build_package

graph = build_package(
    "path/to/project", package_name="my_package", source="src/my_package"
)
```

Set `package_name` to the prefix used by the code's absolute imports when the
project directory has a different name. For example, this connects
`from my_package.helper import compute` to the discovered `my_package.helper`
module. `source` selects files; it does not change the default module prefix.
CLI and MCP users can select the package directory itself as their target,
such as `path/to/project/src/my_package`, to infer the matching prefix while
analyzing only that directory tree.

File access errors raise `OSError`; invalid Python raises `SyntaxError`.
An existing directory containing no discovered Python files produces an empty
graph successfully. Check the returned module scope count when an empty source
selection may indicate a configuration mistake.
Invalid paths, source layouts, and unsupported constructs can raise `ValueError`
or `NotImplementedError`. Deeply nested input can raise `RecursionError`.
See [analysis boundaries](analysis-boundaries.md) for supported behavior.

## Calculate a profile

```text
summarize(root, scope_id=None, include_children=False, include_parent=False,
          metrics=None, depth=None, include_own_profile=False) -> dict
```

`summarize` returns a JSON-compatible dictionary containing:

- `version`: the Depencity version that produced the summary, included even
  when metrics are filtered out.
- `scopes`: a tree of scopes, each with `id`, `kind`, and `profile`.
- `scope_counts`: counts of scopes covered by the profiles.

`profile` includes a scope's descendants. `children` appears when child scopes
are selected; `own_profile` appears when requested.

| Parameter | Meaning |
| --- | --- |
| `root: Scope` | Graph root returned by a builder. |
| `scope_id: str \| None` | Select an exact ID from a previous summary; `None` selects all scopes. |
| `include_children`, `include_parent` | With `scope_id`, also select its immediate children or parent. They do not recursively select descendants. |
| `metrics: list[str] \| None` | Select [exact metric keys](metrics.md#select-metrics); `None` includes all, `[]` returns scope structure without metrics. |
| `depth: int \| None` | Display depth from the selected roots; `0` shows roots only, `None` shows all selected scopes. |
| `include_own_profile: bool` | Include metrics for each scope without descendants. Aggregate profiles and scope counts always cover descendants, even beyond display depth. |

Use IDs from the current summary to select a scope:

```python
scope_id = summary["scopes"][0]["id"]
selected = summarize(graph, scope_id=scope_id, include_children=True)
```

Invalid scope IDs, metric names, or depth values raise `ValueError`.
IDs can change after source edits.

### Measure one scope or subtree

```text
profile(scope, *, include_paths=True, include_cycles=True,
        scope_metrics=None) -> ScopeProfile
profile_subgraph(root, scope_metrics=None, *, include_paths=True,
                 include_cycles=True) -> ScopeProfile
```

`profile` measures only the supplied scope. `profile_subgraph` measures the
scope and its descendants together. Both return a `ScopeProfile`.

Set `include_paths=False` or `include_cycles=False` to skip those calculations;
skipped metrics remain zero. `scope_metrics` accepts a dictionary cache for
repeated measurements of an unchanged graph; leave it as `None` otherwise.

`ScopeProfile` stores metrics as attributes. Attribute names use `__` in place
of the dots in summary keys:

```python
from depencity import profile_subgraph

measured = profile_subgraph(graph)
reads = measured.variable__total__read__count
```

Use `summarize` for JSON output.
See [metrics](metrics.md) for metric definitions.

## Export a graph

| Function | Result |
| --- | --- |
| `to_dict(root: Scope) -> dict` | JSON-compatible graph containing `version`, `scopes`, `nodes`, and `edges`. |
| `to_json(root: Scope) -> str` | The graph serialized as JSON. |
| `to_dot(root: Scope) -> str` | Graphviz DOT; rendering requires Graphviz separately. |

Exported JSON omits some metadata used to calculate profiles. Calculate profiles
from the graph returned by a builder; JSON alone cannot reproduce every metric.
IDs can change after source edits. See the [graph model](graph-model.md) for
the JSON structure.

## Inspect a graph

`Scope` contains the nodes and child scopes of a module, class, function, or
comprehension. The graph root also contains any builtins used by the source.

```python
for scope in graph.walk_scopes():
    for node in scope.nodes:
        for edge in node.dependency_edges:
            print(edge.dependency.name, "->", node.display_name)
```

`Node` objects are immutable. `Scope` containers are mutable; leave them unchanged
while profiling or exporting.

| Type | Fields and operations |
| --- | --- |
| `Scope` | `name`, `kind`, `parent`, `children`, `nodes`, `is_standalone_module`. `walk_scopes()` yields itself and descendants in declaration order; `path()` returns its display path, which need not be unique. |
| `Node` | `name`, `display_name`, `scope`, `kind`, `operation_type`, `access`, and `dependency_edges`. Classification fields include `is_instance_attribute`, `is_class_attribute`, `is_global_write`, `is_nonlocal_write`, `is_named_endpoint`, `is_version_merge`, `is_generator_expression`, `is_import`, `is_unresolved`, and `output_type`. |
| `DependencyEdge` | Immutable tuple with `dependency`, `count`, `access`, `edge_type`, `is_call_argument`, `is_callee`, `is_variable_read`, `is_callable_read`, `read_contribution_count`, and `callable_read_count`. Stored on the consumer; edge direction is dependency → consumer. |

`Node.is_builtin` identifies nodes owned by the builtins scope. `Node.deps`
returns distinct dependency endpoints, excluding structural edges.
`Node.collect_call_targets()` returns `(resolved_targets, external_targets)` as
tuples of graph objects. Read qualifiers and occurrence counts are explained in
[Edge fields](graph-model.md#edge-fields).

## Enumerations and version

All public enums inherit from `str` and `Enum`:

| Enum | Members |
| --- | --- |
| `ScopeKind` | `ROOT`, `MODULE`, `FUNCTION`, `CLASS`, `COMPREHENSION`, `BUILTINS` |
| `NodeKind` | `VARIABLE`, `RESULT`, `YIELD_FROM_RESULT`, `IMPORT_TARGET`, `UNRESOLVED_VALUE`, `BINDING`, `OPERATION`, `CALL`, `REFERENCE`, `CONDITION`, `COMPREHENSION`, `SUBSCRIPT` |
| `EdgeType` | `DATA`, `ITERATION`, `PREDICATE`, `BINDING`, `DECLARATION` |
| `AccessMode` | `READ`, `WRITE` |
| `OperationType` | `TRANSFORM`, `EXTRACT`, `CONTAINER`, `MUTATION`, `RAISE`, `ASSERT` |
| `OutputType` | `RETURN`, `YIELD`, `RESULT` |

Values are lowercase member names. `EdgeType.is_dependency` is true for `DATA`,
`ITERATION`, and `PREDICATE`; binding and declaration edges are structural.
`NodeKind.is_value` groups `VARIABLE`, `RESULT`, `YIELD_FROM_RESULT`, `IMPORT_TARGET`, and `UNRESOLVED_VALUE`.
`__version__: str` is the installed Depencity version.

Only names documented here are public. Internal modules may change in any
release, including patch releases.
