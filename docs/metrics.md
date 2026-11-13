# Metrics model

Metrics are organized around dependency kinds. Reference shape, access mode,
resolution, and scope provenance are separate dimensions.

```text
dependency
├── variable
│   ├── local
│   │   ├── read
│   │   │   └── count
│   │   └── write
│   │       └── count
│   ├── enclosing
│   │   ├── read
│   │   │   └── count
│   │   └── write
│   │       └── count
│   ├── module
│   │   ├── read
│   │   │   └── count
│   │   └── write
│   │       └── count
│   ├── builtin
│   │   └── read
│   │       └── count
│   ├── other scope
│   │   └── read
│   │       └── count
│   ├── unresolved
│   │   └── read
│   │       └── count
│   └── total
│       ├── read
│       │   ├── count
│       │   └── distinct_count
│       └── write
│           └── count
│
├── attribute
│   ├── total
│   │   ├── read
│   │   │   └── count
│   │   └── write
│   │       └── count
│   ├── class
│   │   ├── read
│   │   │   └── count
│   │   └── write
│   │       └── count
│   └── external
│       ├── read
│       │   └── count
│       └── write
│           └── count
│
├── subscript
│   ├── read
│   │   └── count
│   └── write
│       └── count
│
├── call
│   ├── occurrences
│   │   ├── total
│   │   │   └── count
│   │   ├── resolved
│   │   │   └── count
│   │   └── unresolved
│   │       └── count
│   └── dependencies
│       ├── resolved targets
│       │   └── count
│       └── external
│           ├── count
│           └── distinct_count
│
├── construction
│   └── container creation
│       └── count
│
└── graph
    ├── paths
    │   ├── expressions
    │   │   ├── count
    │   │   └── length
    │   │       └── max
    │   └── data
    │       ├── count
    │       └── length
    │           ├── max
    │           ├── mean
    │           ├── p95
    │           └── distribution
    ├── version merges
    │   └── count
    └── cyclic components
        └── count
```

## Select metrics

Use these exact keys in the Python API or MCP `metrics` parameter. There is no
`dependency.` prefix. `None` selects all metrics; `[]` returns scope structure
without metrics. Unknown keys raise `ValueError`.

| Key | Value type | Meaning |
| --- | --- | --- |
| `variable.local.read.count` | `int` | Reads of bindings owned by the consuming scope. |
| `variable.enclosing.read.count` | `int` | Reads of enclosing-function bindings. |
| `variable.module.read.count` | `int` | Reads of module bindings. |
| `variable.builtin.read.count` | `int` | Reads of predefined builtin bindings. |
| `variable.other_scope.read.count` | `int` | Reads of bindings in other scopes. |
| `variable.unresolved.read.count` | `int` | Read uses without an applicable binding. |
| `variable.total.read.count` | `int` | All variable read uses. |
| `variable.total.read.distinct_count` | `int` | Distinct variable dependencies. |
| `variable.local.write.count` | `int` | Writes to local bindings. |
| `variable.enclosing.write.count` | `int` | Writes to enclosing bindings. |
| `variable.module.write.count` | `int` | Writes to module bindings. |
| `variable.total.write.count` | `int` | All variable writes. |
| `attribute.total.read.count` | `int` | All attribute reads. |
| `attribute.total.write.count` | `int` | All attribute writes. |
| `attribute.class.read.count` | `int` | Attribute reads rooted at recognized method receivers. |
| `attribute.class.write.count` | `int` | Attribute writes rooted at recognized method receivers. |
| `attribute.external.read.count` | `int` | Attribute reads outside the recognized receiver category. |
| `attribute.external.write.count` | `int` | Attribute writes outside the recognized receiver category. |
| `subscript.read.count` | `int` | Subscript reads. |
| `subscript.write.count` | `int` | Subscript writes. |
| `call.occurrences.total.count` | `int` | Static call occurrences. |
| `call.occurrences.resolved.count` | `int` | Call occurrences with at least one known callable target. |
| `call.occurrences.unresolved.count` | `int` | Call occurrences with no known callable target. |
| `call.dependencies.resolved_targets.count` | `int` | Identity-distinct callable targets summed per call. |
| `call.dependencies.external.count` | `int` | External graph target contributions summed across calls. |
| `call.dependencies.external.distinct_count` | `int` | Distinct external graph targets. |
| `construction.container_creation.count` | `int` | Container literals and list, set, and dict comprehensions. |
| `graph.paths.expressions.count` | `int \| None` | Dependency paths ending at expression endpoints. |
| `graph.paths.expressions.length.max` | `int \| None` | Longest path at an expression endpoint, in edges. |
| `graph.paths.data.count` | `int \| None` | Summed path counts at named endpoints, including intermediate values. |
| `graph.paths.data.length.max` | `int \| None` | Longest path at a named endpoint, in edges. |
| `graph.paths.data.length.mean` | `float \| None` | Mean path length at named endpoints, in edges. |
| `graph.paths.data.length.p95` | `int \| None` | Nearest-rank 95th percentile of path lengths at named endpoints. |
| `graph.paths.data.length.distribution` | `dict[int, int] \| None` | Path length to path count at named endpoints; JSON object keys are strings. |
| `graph.version_merges.count` | `int` | Nodes consuming multiple versions of the same binding. |
| `graph.cyclic_components.count` | `int` | Strongly connected components containing a cycle. |
| `graph.cyclic_components.nodes.count` | `int` | Total nodes in those components, recomputed for the selected scope set. |

For example, call the MCP `profile` tool with an existing workspace file:

```json
{
  "path": "path/to/file.py",
  "metrics": ["variable.total.read.count", "graph.cyclic_components.count"],
  "depth": 2
}
```

The sections below define counting rules and interpretation. For an introduction
to scope aggregation and depth, see [Interpret profiles](interpreting-profiles.md).

## Scope profiles

Each scope's `profile` includes that scope and all descendant scopes. Enable
`include_own_profile` to also return `own_profile`, which measures only the scope
itself. The root's `profile` provides totals across the graph.

Path length is measured in graph edges. Call sites count static call
occurrences. Attribute class/external counts use recognized method receiver
bindings, regardless of parameter spelling: the first positional parameter of
an instance method or a recognized builtin `classmethod` is the
receiver. Attribute chains rooted at that binding count as class, including
reads in closures that capture it. Static methods, ordinary functions, shadowed
or replaced receiver bindings, and aliases are not recognized as receivers.
Other decorators preserve declaration identity. This is a receiver
classification, not general ownership inference. A call contributes
a value dependency through its call result; it is not a separate graph edge
kind. Unresolved source names use local unresolved value nodes, which participate
in path measurements together with their dependency edges.
Version merges count nodes that consume multiple versions of the same binding.
One input with several possible binding versions contributes one read, not one
read per candidate.
Cyclic components count strongly connected components that contain a cycle.
`graph.cyclic_components.nodes.count` reports their total size, including binding
nodes. Both metrics are recomputed for aggregate scopes, so cycles spanning
scopes are counted together and growing regions remain visible even when the
component count stays unchanged.

Path traversal follows `data`, `iteration`, and `predicate` dependencies,
visiting each dependency endpoint once per consuming node. The JSON export
also includes structural `binding` and `declaration` edges, which path
traversal excludes. Callable scopes in the measured scope set act as zero-depth
dependency endpoints. References to scopes outside that set do not add path
steps. An edge's occurrence `count` does not multiply paths.

`graph.paths.data.count` sums dependency-path counts at every named data
endpoint, including intermediate values. A shared path prefix contributes at
each endpoint it reaches.

`graph.paths.expressions.length.max` measures the longest path ending at an
expression endpoint, including terminal cyclic components as described below. It includes computations ending in yields and writes, even when
their outputs are not named data endpoints.

Expression and data paths traverse the same dependency graph and select
different endpoints; they are overlapping measurements, not disjoint path
categories. A path ending at a named graph sink contributes to both metrics.
The data-path length statistics describe paths ending at named endpoints,
including intermediate values that have later consumers.

Paths follow dependencies backward from each endpoint. At a branch, count each
dependency separately. A root contributes one path of length zero; each traversed
edge adds one to length. Binding nodes are excluded.

A path stops when it reaches a root or revisits a node already on that path.
The edge closing a cycle counts toward length. Other paths can still use that
node and its dependencies. For example, an isolated two-node cycle contributes
two expression paths, each of length two.

Expression paths end at graph sinks. A cyclic component with no outside consumer
has no ordinary sink, so every member also serves as an expression endpoint.
Named data endpoints are unchanged. Counts are independent of traversal order.

Exact counting can require exponentially many visited-node sets. For each cyclic
component, computation allows 50,000 distinct `(node, visited set)` states and
1,000,000 work units. A work unit is one dependency examined during state
discovery or one path-length bucket added during evaluation. These deterministic
limits apply to the complete component, not individual routes. Acyclic regions
do not use these limits.

If either limit is exceeded, affected path metrics are **unavailable**: Python
returns `None`, JSON and MCP return `null`, and CLI text displays `unavailable`.
If an expression endpoint depends on an unavailable region, both expression
metrics are unavailable. If a named endpoint depends on one, all five data-path
metrics are unavailable. Partial sums and distributions are discarded; unrelated
metrics and scopes remain available. Metric filters preserve `null` values.

Becoming unavailable under the same limits can signal more branching or
overlapping cycles. It is a measurement limit, not a numerical score or proof
of worse code. Compare the source, cyclic-region sizes, and other available
metrics; an unavailable path count cannot establish a numerical improvement.

A direct profile measures one scope; an aggregate measures that scope and its
descendants together. Aggregate paths and cycles are recomputed across scopes,
rather than obtained by adding the individual profiles.

`call.occurrences.total.count` counts call nodes. `call.dependencies.external.count`
counts their external graph targets: one call reaching two output nodes
contributes one occurrence and two dependencies. `distinct_count` counts unique
target nodes, so repeated calls to the same target increase `count` but not
`distinct_count`. Unresolved calls without an external graph target still count
as occurrences. Calls imported from outside the analyzed package count as
unresolved because their implementations are unknown, but still contribute
their known external targets. Builtins and cross-module calls can also
contribute external targets. Occurrences and
external dependencies are separate counts; targets use node identity.

`call.occurrences.resolved.count` counts each call node at most once, even when
control-flow alternatives resolve it to several implementations. A call is
resolved when at least one callable target is known: a builtin, a known callable
output reached through an import target, or a direct callable scope or output.
Known targets still contribute when other alternatives are unresolved. In
`call.dependencies.resolved_targets.count`, each identity-distinct callable
scope counts once for that call; aliases to the same scope are deduplicated,
and multiple return or yield outputs from one callable still count as one
target. Imported class aliases retain source class identity through declaration
edges, which do not add data paths. Unknown alternatives remain represented by
their own dependency edges.

The `root` scope contributes to scope counts. Its direct profile includes its
shared target nodes; its subgraph profile includes all modules and builtins.
Import-to-target and call-to-target dependencies contribute ordinary graph
edges and can extend whole-graph data paths.

## Why metrics use read/write terminology

We use read/write metrics because they describe value access and state changes
across variables, attributes, and subscripts without requiring every change to
be a definition. Variable assignments and parameters bind values, deletions
invalidate bindings or remove entries, and attribute and subscript writes mutate
objects. Replacing write counts with definition counts would exclude deletions
and require deciding what object state a mutation defines. Read counts already
measure modeled dependency uses, including unresolved reads, rather than source
occurrences; calling them uses would not itself improve their precision.
A definition/use counting contract would therefore add distinctions without a
demonstrated benefit for assessing code dependencies. We retain read/write
metrics while tracking binding versions and their dependencies in the graph.

## Variable write counts

Assignments, parameter bindings, and explicit bare-name deletions contribute
variable writes. Each deleted name contributes one write, classified as local,
module for a declared global, or enclosing for a declared nonlocal. The deletion
mutation retains its dependency on the prior binding without contributing a
variable read or distinct read. An unbound deletion does not contribute an
unresolved read. A comprehension walrus assignment is counted once in its
destination scope; its comprehension evaluation scope does not add another write count.
Function and class declarations bind names through declaration edges and do not
contribute variable writes, whether the declaration is unconditional or conditional.
Attribute and subscript deletions contribute their respective reference write
counts.

## Variable read counts

Read categories use the binding's owner relative to the consuming scope, even
when another scope wrote its current value. A scope reading its own binding
counts a local read; `global` and `nonlocal` write flags do not classify reads.

Variable read counts measure dependency uses: how many times a variable
contributes to relationships represented in the graph. They do not count source
name occurrences or runtime evaluations. A single value can contribute to more
than one relationship and therefore count as more than one read use. For
example, the middle value in `a < b < c` contributes to both comparisons, and
the iterable in `[value for (first, *rest) in groups for value in rest]`
contributes to the dependencies of both unpacked targets, `first` and `rest`.
The corresponding distinct-read metric counts unique semantic dependencies,
not the number of uses.

See [edge qualifiers and read contributions](graph-model.md#edge-qualifiers-and-read-contributions)
for how these metrics relate to exported graph edges.

Unresolved read counts count uses with no applicable binding, not unresolved
value nodes. Repeated uses still count individually; distinct reads deduplicate
the same unresolved spelling within a scope.

Type annotations provide type information for member resolution. Annotation
names are not graph dependencies and do not contribute to variable read counts.

Builtin names that resolve through Python's predefined namespace have graph
binding nodes marked `is_builtin`. Their reads count toward total reads and the
builtin read metric, but not module or unresolved reads.

## Call occurrences and resolved targets

The two metrics answer different questions:

- `call.occurrences.resolved.count`: How many call expressions are resolved?
- `call.dependencies.resolved_targets.count`: How many possible callable targets
  do those expressions have, summed per call?

Assuming `f` and `g` are known callable targets:

| Source | Resolved call expressions | Resolved target contributions |
| --- | --- | --- |
| `f()` | 1 | 1 |
| `f(); f()` | 2 | 2 |
| `callback = f if condition else g; callback()` | 1 | 2 |

Targets are deduplicated within each call, not across the whole scope. Therefore,
`f(); f()` contributes two targets even though it calls only one unique callable.
Neither metric counts runtime executions.

## Details

`construction.container_creation.count` counts direct container literals and
list, set, and dict comprehensions. Generator expressions are excluded because
they create lazy iterators. Calls such as `list(items)` are counted as calls,
not as container creation; the metric does not infer allocation from call
targets.
