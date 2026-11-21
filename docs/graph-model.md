# Dependency graph model

Depencity builds a static graph of how operations produce and use values.
The graph shows program structure and helps compare it before and after a
refactoring. The model builds on data dependence graphs, with scope ownership
and explicit nodes for conditions and effects.

A data dependency means that one program item uses a value produced by another.
For example, in `total = left + right`, `total` depends on `left` and `right`
through the addition operation. Conditions also contribute dependencies to the
items they govern. An edge's `access` describes how its dependency is used,
independently of the consumer node's access. In `x = source`, the assignment
writes `x` but reads `source`; `del x` has a write-qualified dependency on `x`.
Structural relationships may have no access qualifier.

- [Core entities](#core-entities)
- [Node kinds](#node-kinds)
- [Node fields](#node-fields)
- [Edge fields](#edge-fields)
- [Source coverage](#source-coverage)
- [Limits](#limits)
- [Exports](#exports)

## Core entities

- **Scope** groups nodes and child scopes.
- **Node** represents a program item.
- **Edge** connects a node or scope to a node.

Scopes form a tree rooted at `__root__`. Its children are the source modules
and, when used, the `builtins` scope. Classes, functions, methods, and
comprehensions introduce nested scopes. Each node belongs to one scope.
A callable scope also identifies the nodes that supply its outputs.
Name lookup and module-relative edge classification stop at the source module.
Module and function display paths omit the `__root__` prefix.

In `y = x`, the assignment creates a new value node for `y`. A dependency
edge points from the visible value of `x` to that new node. The scope records
which nodes it owns independently of these edges. A scope can itself supply a
dependency, as when a function is passed as a value.

Reassigning `y` creates another value node in the same scope. The two nodes
share a name but have distinct identities. Structural edges link the binding
for `y` to its value versions and connect declared scopes to their bindings.

## Node kinds

Some nodes represent source bindings; others represent synthetic results or
effects. Generated names such as `__op_0__` are implementation details.
`name` is the internal graph name, while `display_name` is intended for graph
presentation. Names are not unique identifiers and may change across source
edits or analyzer versions. Operations use their source expression as the display name;
other nodes use their explicit display name, binding, or internal name.

| Kind | Example | Role |
| --- | --- | --- |
| `binding` | Shared identity of `x` across assignments | Groups value versions and callable scopes; not a data dependency |
| `variable` | `result = value`, function parameters | Named variable version |
| `result` | `return result`, `yield item`, `await task` | Callable output or expression result, including the value received by `yield` |
| `yield_from_result` | `result = yield from source` | Delegated generator's return value |
| `import_target` | Canonical `module.name` | Shared imported target |
| `unresolved_value` | Read of an unknown name | Local placeholder for a value whose source the analyzer cannot resolve. The node carries `is_unresolved: true` and supplies the value dependency to the consumer. |
| `operation` | `left + right`, `left, right = value`, `[left, right]`, `del value` | Transformation, extraction, container, or effect |
| `call` | `parse(text)` | Call with callable and argument dependencies; resolved calls may also depend on callee outputs |
| `reference` | `record.value` | Attribute read or write with an object dependency |
| `condition` | `if ready:` | Predicate and its dependencies |
| `comprehension` | `[item * 2 for item in items]` | Result linked to an output in a separate comprehension scope |
| `subscript` | `items[index]` | Read or write with container and index dependencies |

A statement is not a graph entity. The model defines no statement scope or
statement node. It analyzes the program as a graph of operations and records
dependencies between the resulting graph items. This is a deliberate
simplification. A scope would be the natural way to group a statement's
operations, but a scope for every statement would add noise to the graph
and require scope classification.

## Node fields

| JSON field | Meaning |
| --- | --- |
| `id` | Unique identifier for the node within the export. |
| `name` | Internal graph name. |
| `display_name` | Name shown in graph presentations. |
| `scope` | Identifier of the owning scope. |
| `kind` | One of the [node kinds](#node-kinds). |
| `access` | Node access mode: `read`, `write`, or `null` when neither applies. |
| `operation_type` | Operation category, when present: `transform`, `extract`, `container`, `mutation`, `raise`, or `assert`. |
| `dependencies` | Identifiers of the nodes or scopes this node depends on. |
| `is_instance_attribute` | Marks an instance attribute. |
| `is_class_attribute` | Marks a class attribute. |
| `is_global_write` | Marks a write to a global binding from another scope. |
| `is_nonlocal_write` | Marks a write to a nonlocal binding. |
| `is_builtin` | Present and true when the owning scope is the predefined `builtins` scope. |
| `is_unresolved` | Present and true when the node stands for a value whose source could not be resolved. |

- Ordinary assignments create `variable` nodes named after their binding, such as
  `x`, with `access=write`. Reassignments create distinct nodes for the same
  binding. Global and nonlocal updates use synthetic write names instead. Their
  profile counts are classified as module writes (`global`) and enclosing writes
  (`nonlocal`); there is no separate other-scope write count.
- Attribute and subscript assignments and deletions use `reference` and
  `subscript` nodes respectively, with `access=write`. Bare-name deletion uses
  a mutation operation with the deleted name as its write target and contributes
  one variable write.
- A return with a value creates a synthetic `result` node carrying the returned
  expression's dependencies. Bare returns and possible function fallthrough
  create a `None` output.
- Callable outputs include returned and yielded values. Intermediate
  expression results, including awaited values, stay within the scope where
  they are computed; effects are represented in the graph but are not callable
  outputs.

## Edge fields

| JSON field | Meaning |
| --- | --- |
| `source` | Identifier of the node or scope the edge starts from. |
| `target` | Identifier of the node the edge points to. For a dependency edge, this is the consumer. |
| `edge_type` | Relationship kind. Dependency edges use `data`, `iteration`, or `predicate`. Structural edges use `binding` or `declaration`. |
| `count` | Number of occurrences represented by the edge, at least one. |
| `access` | How the target uses the source: `read`, `write`, or `null` when unqualified. |
| `is_callee` | The source supplies the callable being invoked. |
| `is_call_argument` | The source supplies a call argument. |
| `is_variable_read` | The edge represents a possible variable read. |
| `is_callable_read` | The edge represents a possible callable read. |
| `read_contribution_count` | Number of variable reads credited to this edge. |
| `callable_read_count` | Number of callable reads credited to this edge. |

## Source coverage

The root owns one shared value node per canonical import target. Import
bindings stay in their lexical scopes. For example, `from x import my_func as f`
and `from x import my_func as g` both depend on the root's `x.my_func` node.
The graph omits unused imports and their unreferenced targets.

For modules in the analyzed package, direct imports and `module.VALUE` reads
depend on the visible source binding through the shared target. An internal
target's declaration scope feeds that target. For reassigned
names, this path leads to the currently visible binding versions. Depencity
constructs canonical names statically and leaves external implementations opaque.

Imported calls retain the path from binding to target and depend on known
callee outputs. Passing a callable as a value creates no dependency on those
outputs. Qualified calls use the reference's member dependency when available.
Otherwise, they use a canonical member target. For example, with `import x as api`,
the fallback target for `api.run()` is the root's `x.run` node.

Star imports use an isolated literal `__all__` list or tuple when available.
Otherwise, they include discovered public module names. If the exports are
uncertain, the graph retains an unresolved `module.*` dependency. Both names
and uncertainty propagate through re-exports without executing Python code.

- **Bindings and declarations**: assignments, parameters, imports, defaults,
  decorators, and class bases contribute graph dependencies. Type aliases bind
  their runtime alias object without evaluating the lazy alias value. Generic
  function and class type parameters are bindings visible in their bodies.
  Annotation names provide type information for member resolution but do not
  create graph dependencies or contribute to variable-read metrics.
- **Calls and captures**: resolution links lexical bindings, enclosing values,
  and some internal package calls. Conditional expressions and boolean
  `and`/`or` operations propagate known callable targets from possible result
  operands; their conditions do not become callable targets. Unknown
  alternatives remain graph dependencies. Recursive calls can create cycles.
- **Branches and loops**: predicates, iterables, and binding updates contribute
  dependencies. Loop-body updates are conditional on iteration; zero-iteration
  fallthrough is retained, while loop-carried dependencies remain approximate.
  Conditional-expression branches share a condition dependency, so the graph
  does not distinguish the test's true and false outcomes.
- **Exceptions and matching**: explicit exception expressions, handler types,
  match subjects, pattern bindings, and guards contribute dependencies.
- **Comprehensions, generators, and async code**: comprehension scopes and
  yield/await expressions retain their dependencies. Each `async for` statement
  and each async comprehension clause creates a transform operation labeled
  `async iteration`. It depends on the iterable, and the loop target depends on
  its result through an extraction operation. Synchronous iteration targets
  also use extraction operations. Loop and comprehension `for` conditions gate
  body operations. Filters and subsequent comprehension clauses retain their own
  dependencies in the same scope, including in generator expressions.
  A `yield` output and the
  expression result received when the generator resumes are separate nodes;
  the incoming value is unknown. `yield from` also has a separate expression
  result linked to the delegated source. Walrus writes are
  conditional on comprehension iteration, preserving the prior binding as a
  possible value. Generator-expression writes use the same conservative model
  even when the generator is never consumed; evaluation timing is not inferred.
- **Classes**: a class is a scope and its methods are child function scopes.
  A known constructor call links to the class and its `__init__` method.
  Direct constructor expressions, constructor assignments, and direct
  annotations provide limited receiver types for method lookup. Simple named or
  qualified class return annotations on synchronous, non-generator functions
  also supply receiver types; function bodies do not infer return types.
  Class alternatives in `A | B`
  annotations are supported; a conditional annotation conservatively retains
  prior receiver types, including when a loop may run zero times. Other union
  forms are not inferred. Named bases,
  including `Base[T]` and
  `pkg.Base[T]`, support declaration-order inheritance lookup and single-base
  `super()` calls; dynamic bases remain unresolved.
  In an instance method, the first positional parameter represents the instance.
  In a recognized `classmethod`, it represents the class. Parameter spelling
  does not affect either rule. Static methods and nested functions have no
  implicit receiver parameter. Method values retain member and receiver
  dependencies; runtime binding is not modeled. Subscript types are inferred
  for lists, tuples and sequences. Methods and their nested functions resolve
  the implicit `__class__` cell; other class names are not closure bindings.
- **Decorators**: preserve declaration identity; replacement results are not
  inferred. Proven builtin `staticmethod`/`classmethod` identity selects receiver behavior.
- **Unresolved names**: within each lexical scope, all uses of the same unresolved
  name share one local value node. These nodes feed
  their consumers and participate in graph and path measurements. Unknown
  callable targets add no extra nodes; calls consume their callee values.

## Limits

See [Analysis boundaries](analysis-boundaries.md) for the detailed rules and approximations.

- Type inference is static and limited to direct constructors and annotations;
  unknown receivers remain unresolved, and arbitrary descriptors are not run.
- Multiple inheritance uses declaration-order lookup; full Python MRO semantics
  and dynamic bases are not modeled.
- No complete execution-order, exception-path, or scheduling model.
- No object-identity tracking through aliases or argument-to-parameter mapping.
- External packages are not loaded. Statically named imported callables have
  shared root target nodes, but their implementations remain unresolved.
  Other missing bindings use the local placeholder nodes
  described above. Python builtins resolve to the `builtins` scope. Unresolved
  calls remain visible in both JSON and DOT exports.
- Resolution is approximate. The graph is not guaranteed to contain every
  possible runtime dependency.

## Exports

The Python builders `build`, `build_target`, and `build_package` return the
graph's root `Scope`.

Pass the root directly to `to_dict`, `to_json`, `to_dot`, `summarize`, or
`profile_subgraph`. Use `root.walk_scopes()` to iterate the root and all its
descendants in declaration order; it follows ownership children, not dependency
edges. `profile(scope)` still measures only the scope's direct nodes.

With Depencity installed, save `x = 1` as `example.py` in the current directory,
then run:

```python
from depencity import build_target, to_dict

root = build_target("example.py")
document = to_dict(root)
for scope in root.walk_scopes():
    print(scope.path())
```

JSON includes `version`, `scopes`, `nodes`, and `edges`. Profiles are exported
separately by `summarize`. The top-level `version` identifies the Depencity
version that produced the output. The current 0.x
representation has no backward-compatibility guarantee: consumers should pin
the package version and validate fields before relying on them.

An abbreviated populated export looks like this:

```json
{
  "version": "0.1.0",
  "scopes": [
    {
      "id": "__root__",
      "name": "__root__",
      "kind": "root",
      "parent": null,
      "children": ["__module__"],
      "nodes": []
    },
    {
      "id": "__module__",
      "name": "__module__",
      "kind": "module",
      "parent": "__root__",
      "children": [],
      "nodes": ["__module__.x#0", "__module__.__binding_x__#1"]
    }
  ],
  "nodes": [
    {
      "id": "__module__.x#0",
      "name": "x",
      "display_name": "x",
      "scope": "__module__",
      "kind": "variable",
      "access": "write",
      "is_instance_attribute": false,
      "is_class_attribute": false,
      "dependencies": []
    },
    {
      "id": "__module__.__binding_x__#1",
      "name": "__binding_x__",
      "display_name": "x",
      "scope": "__module__",
      "kind": "binding",
      "access": null,
      "is_instance_attribute": false,
      "is_class_attribute": false,
      "dependencies": []
    }
  ],
  "edges": [
    {
      "source": "__module__.__binding_x__#1",
      "target": "__module__.x#0",
      "count": 1,
      "access": null,
      "is_call_argument": false,
      "is_callee": false,
      "is_variable_read": false,
      "is_callable_read": false,
      "read_contribution_count": 0,
      "callable_read_count": 0,
      "edge_type": "binding"
    }
  ]
}
```

- Scopes record parents, children, and owned nodes. Binding nodes and `binding`
  edges connect names to their value versions; scopes do not export a `bindings` field.
- Nodes record their scope, kind, access, attribute classification, display labels,
  and resolved dependencies. Instance attributes are accesses rooted at the
  recognized first positional parameter of an instance method; class attributes
  are rooted at the corresponding parameter of a builtin `classmethod`.
  Parameter spelling does not determine classification. See the
  [receiver classification rules](metrics.md#scope-profiles) for limitations.
- Profile fields ending in `distinct_count` are numeric counts. External call
  targets are deduplicated by graph identity; internal identity keys are not
  exported.
- Current identifiers derive from lexical paths and node positions; they are
  not stable across edits.

The following commands assume a development checkout with `uv sync --locked`
completed. Replace `path/to/file.py` with an existing source file. For an
installed tool, run `depencity` directly without the `uv run` prefix.

Use JSON for programmatic inspection:

```bash
uv run depencity graph path/to/file.py --format json
```

Use DOT for visual inspection. It does not include the JSON version field:

```bash
uv run depencity graph path/to/file.py --format dot
```
