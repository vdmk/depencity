# Usage

Depencity supports analysis of Python files and packages through its CLI or an MCP client. The commands
below assume Depencity is installed; see [installation](../README.md#install).
In a development checkout, prefix CLI commands with `uv run`.

- [Analyze a file](#analyze-a-file)
- [Analyze a package](#analyze-a-package)
- [Export a graph](#export-a-graph)
- [Use with an MCP client](#use-with-an-mcp-client)
- [Troubleshooting](#troubleshooting)

## Analyze a file

```bash
depencity profile path/to/file.py
depencity profile path/to/file.py --format json
depencity profile path/to/file.py --depth 2 --include-own-profile
```

The default output is text grouped by scope (`--format text`). With
`--include-own-profile`, Aggregate and Own columns distinguish the two profiles.
The former Markdown format has been replaced by text. JSON returns the nested
summary used by the Python API and MCP. `--depth` limits displayed scope detail;
aggregate profiles still include descendants. `--include-own-profile` adds
measurements for each scope without its descendants. See
[profile interpretation](interpreting-profiles.md) for counting and comparison
rules.

## Analyze a package

For a package with sources in `my_package/src/my_package`:

```bash
depencity profile my_package --source src/my_package --depth 1
depencity graph my_package --source src/my_package --format json
```

For directory targets, `--source` selects a source directory relative to the
target. Module names use the target directory name as their prefix, regardless
of `--source`. Internal imports are connected across the discovered modules;
external libraries are represented as dependencies without loading their code.
Discovery skips a fixed set of directory names, including `env` and `venv`;
see the [discovery exclusions](analysis-boundaries.md#import-resolution).

If the checkout is named `my-project` but the code imports `my_package`, target
the package directory itself so the inferred prefix matches those imports:

```bash
depencity profile my-project/src/my_package --depth 1
depencity graph my-project/src/my_package --format json
```

Using `my-project --source src/my_package` would instead prefix modules with
`my-project`, so absolute imports such as `from my_package.helper import compute`
may be treated as external. Selecting the package directory analyzes only that
tree. To keep a separate project root and specify the import prefix explicitly,
use the Python API's `build_package(..., package_name="my_package", ...)`.

## Export a graph

```bash
depencity graph path/to/file.py --format json
depencity graph path/to/file.py --format dot > graph.dot
```

From the checkout root, export the
[README example](../README.md#export-a-graph):

```bash
uv run depencity graph docs/cases-examples/readme-example.py --format dot > graph.dot
```

To render the DOT export yourself, install Graphviz separately and run:

```bash
dot -Tsvg graph.dot -o graph.svg
```

## Use with an MCP client

Configure your MCP client to launch the installed server over stdio:

```json
{
  "mcpServers": {
    "depencity": {
      "command": "depencity-mcp",
      "args": ["--workspace", "/absolute/path/to/your/project"]
    }
  }
}
```

The exact configuration location and format depend on the client. The server
exposes a `profile` tool returning JSON. It accepts `path` and `source`, scope
selection through `scope`, `include_children`, and `include_parent`, a `metrics`
filter, and the `depth` and `include_own_profile` options.

After connecting, check that your client lists the `profile` tool. Call it on
an existing Python file inside the configured workspace, replacing the path:

```json
{"path": "path/to/file.py", "depth": 2}
```

The tool returns scope counts and a scope tree with profiles as JSON.

The [package-naming rule](#analyze-a-package) also applies to MCP. For a workspace containing
`src/my_package`, pass the package directory as the tool's `path`:

```json
{"path": "src/my_package", "depth": 1}
```

This selects `my_package` as the module prefix. Passing `path="."` with
`source="src/my_package"` uses the workspace directory's name as the prefix,
which may not match the code's absolute imports.

Relative paths start at the server workspace unless the request selects a
subdirectory with `workspace`.
The target must remain inside the selected workspace. `source` selects a source
directory relative to a directory target and is ignored for file targets.
`scope` selects an exact ID from a previous profile; `include_children` and
`include_parent` add its immediate children or parent. `metrics=None` includes
all metrics; an empty list returns scope structure without metrics. See the
[summary parameters](python-api.md#calculate-a-profile) for depth and
aggregation semantics; the Python API calls the scope selector `scope_id`.

The MCP server confines access to its configured workspace. CLI commands accept
absolute paths and resolve relative paths from the current directory.

## Troubleshooting

| Symptom | Check or next action |
| --- | --- |
| `depencity` or `depencity-mcp` is not found | Confirm installation with `uv tool list` and ensure the tool executable directory is on your shell or MCP client PATH. You can configure the client with the executable’s absolute path. |
| MCP rejects a path outside its workspace | Choose a target inside the configured `--workspace`. The optional request `workspace` must also be inside that directory; it does not expand access. |
| Internal imports appear external | Check the [package prefix](#analyze-a-package). `--source` changes discovery, not the prefix. |
| Expected Python files are missing | Check the target, `--source`, and [discovery exclusions](analysis-boundaries.md#import-resolution). Discovery does not use `.gitignore`. |
| Paths become shorter despite more complex code | Inspect `graph.cyclic_components.count`: cyclic nodes and edges touching them are excluded from path statistics. See [metric boundaries](analysis-boundaries.md#metric-boundaries). |

