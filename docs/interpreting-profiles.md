# Interpret profiles

A profile reports scope counts and measurements of data accesses, calls,
container construction, and dependency paths.

| Measurement | What it describes |
| --- | --- |
| Variable reads | Dependency uses grouped by local, enclosing, module, builtin, other-scope, or unresolved bindings; also reports total and distinct reads. |
| Variable writes | Binding updates and deletions grouped by local, enclosing, or module scope, plus a total. |
| Attribute and subscript reads and writes | Accesses through members and indexed values. |
| Call occurrences and targets | Static calls by resolution status, resolved target contributions, and total and distinct external targets. |
| Container construction | Container literals and list, set, and dict comprehensions; excludes generator expressions and constructor calls such as `list(items)`. |
| Expression paths | Paths ending at graph sinks or at members of a cyclic component with no outside consumer. Reports count and maximum length. |
| Data paths | Dependency paths ending at named values, including intermediate values; reports summed path counts, mean length, maximum, p95, and a length distribution. |
| Version merges | Dependencies on multiple possible definitions of one binding. |
| Cyclic components | Groups of nodes containing dependency cycles. |

Read/write describes modeled data accesses and changes, including binding
updates, deletions, and explicit object mutations. Reads count dependency uses,
not source name occurrences or runtime evaluations. Path lengths are measured
in edges; path counts describe dependencies, not possible execution paths.

Each scope's `profile` includes its descendants. Add `--include-own-profile`
to also report `own_profile`, which measures only that scope:

```bash
depencity profile path/to/file.py --include-own-profile --depth 2
```

In text output, **Aggregate** corresponds to JSON `profile`, and **Own** to
`own_profile`. Without `--include-own-profile`, only aggregate values appear.

For example, from the checkout root, profile the
[small arithmetic example](cases-examples/readme-example.py):

```bash
uv run depencity profile docs/cases-examples/readme-example.py --include-own-profile --depth 0
```

Output:

```text
Scopes: 1 function, 1 module, 1 root, 3 total

__root__ [root]
  Metric                                              Aggregate          Own
  Variable
    ...
    Total read count                                          4            0
    ...
    Total write count                                         4            0
  ...
```

The root’s aggregate includes the function’s four reads and four writes; the
root itself has none. Although `--depth 0` displays only the root, all three
scopes contribute to the scope counts and aggregate measurements.

For a complete target, `--depth 0` displays the graph root, `--depth 1` also
includes modules and the builtins scope when present, and `--depth 2` includes
top-level functions and classes. The default displays the full scope tree.
MCP scope selections measure depth from the selected roots. Aggregate
measurements and scope counts still include descendants beyond the displayed
depth; overlapping scope trees are counted once.

For a refactoring comparison, profile the same target and options before and
after the change. Inspect affected scopes as well as totals, path lengths, and
cycles. Paths through a cycle include the edge that first revisits a node and stop
there. If counting exceeds the computation limits, the affected path metrics
are unavailable.

See [metric definitions](metrics.md) for the complete metric names and
counting rules.

For a worked comparison with measured before/after results, see
[Compare a refactoring](refactoring.md).
