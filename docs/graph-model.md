# Dependency graph model

This package represents programs as static dependency graphs. The idea is that
data dependencies help describe program structure and compare refactorings.
The model builds on data dependence graphs, with scope ownership and explicit
nodes for conditions and effects.

A data dependency means that one program item uses a value produced by another.
For example, in `total = left + right`, `total` depends on `left` and `right`
through the addition operation. Conditions also contribute dependencies to the
items they govern. An edge's `access` describes how its dependency is used,
independently of the consumer node's access. In `x = source`, the assignment
writes `x` but reads `source`; `del x` has a write-qualified dependency on `x`.
Structural relationships may have no access qualifier.

- [Core entities](#core-entities)
- [Node kinds](#node-kinds)
- [Source coverage](#source-coverage)
- [Limits](#limits)
- [Exports](#exports)

## Core entities

- **Scope**: a graph root, module, class, function or method, comprehension, or predefined
  builtins environment. A scope owns its nodes and may identify the value nodes
  it exposes as callable outputs.
- **Node**: a binding, expression, call, reference, effect, or output owned by a
  scope.
- **Edge**: a resolved dependency from a node or scope to a node that uses it.
- **Unresolved dependency**: a local value node marked `is_unresolved: true`
  when no target is found. Its edge to the consumer represents the dependency.

Names resolved from Python's predefined namespace target binding nodes in the
`builtins` scope. Those graph nodes carry `is_builtin: true`.
The exported graph represents dependencies through edges;
it does not include a parallel list of raw dependency names.

Every graph has one `__root__` scope of kind `root`, whose children are the
source modules and, when used, the builtins scope. The root owns one shared
value node per canonical imported target, whether or not its source is part of
the analyzed package. Local import bindings keep their lexical scopes and
depend on these shared nodes. When the target is in the analyzed package, its
declaration value feeds the shared target; external implementations remain
unknown. For example,
`from x import my_func as f` and `from x import my_func as g` both depend on
the same `x.my_func` node. Imported calls retain the binding-to-target path
and depend on known callee outputs. Passing a callable value does not invoke
its outputs. Qualified calls use the reference's member dependency when
available, otherwise a canonical member target: with
`import x as api`, `api.run()` depends on the root's `x.run` node.
Canonical names are constructed statically; external packages are never loaded.
Unused imports and their unreferenced root targets are omitted.
Star imports use an isolated literal `__all__` list or tuple when available;
otherwise they include discovered public module names. Uncertain exports also
retain an unresolved `module.*` dependency. Names and uncertainty propagate
through re-exports; Python code is never evaluated to determine exports.

For internal package modules, direct imported values and direct
`module.VALUE` reads connect through the canonical root target to the visible
source binding. Reassigned names use the currently visible binding versions.
External module attributes remain opaque because their modules are not loaded.

The root is a graph container, not a Python lexical namespace. Name lookup and
module-relative edge classification stop at the source module. Existing module
and function display paths do not acquire a `__root__` prefix. Node identity,
rather than display names or the number of incoming edges, distinguishes targets.

Edges point from the dependency to its consumer:

```text
dependency -> consumer
```

Scopes record ownership separately from dependency edges. A reference to a
function as a value can produce an edge from its scope to the consuming node.

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
| `unresolved_value` | Read of an unknown name | Unresolved dependency |
| `operation` | `left + right`, `left, right = value`, `[left, right]`, `del value` | Transformation, extraction, container, or effect |
| `call` | `parse(text)` | Call with callable and argument dependencies; resolved calls may also depend on callee outputs |
| `reference` | `record.value` | Attribute read or write with an object dependency |
| `condition` | `if ready:` | Predicate and its dependencies |
| `comprehension` | `[item * 2 for item in items]` | Result linked to an output in a separate comprehension scope |
| `subscript` | `items[index]` | Read or write with container and index dependencies |

- `access` distinguishes reads and writes where applicable.
- `operation_type` distinguishes `transform`, `extract`, `container`, `mutation`, `raise`,
  and `assert` operations.
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

## Source coverage

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
  Functions declared directly in a class infer their first positional
  parameter as an instance of that class, regardless of its name; static
  methods and nested functions do not. Method values retain member and receiver
  dependencies; runtime binding is not modeled. Subscript types are inferred
  for lists, tuples and sequences. Methods and their nested functions resolve
  the implicit `__class__` cell; other class names are not closure bindings.
- **Decorators**: preserve declaration identity; replacement results are not
  inferred. Proven builtin `staticmethod`/`classmethod` identity selects receiver behavior.
- **Unresolved names**: a missing binding gets one local unresolved value node
  per spelling and lexical scope. Uses in that scope reuse it; another scope
  gets a separate node. These nodes feed
  their consumers and participate in graph and path measurements. Unknown
  callable targets add no extra nodes; calls consume their callee values.
  Statically named imports connect a local import binding to a shared root target. An internal
  target's declaration scope feeds that target; an external implementation remains
  unknown.

## Limits

The graph records static relationships; it does not prove runtime behavior.

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
- Edges contain `source` and `target` identifiers. Their `count` records how many
  dependency occurrences the edge represents. Each edge has a count of at least
  one, and repeated source occurrences increase it.
- Profile fields ending in `distinct_count` are numeric counts. External call
  targets are deduplicated by graph identity; internal identity keys are not
  exported.
- Current identifiers derive from lexical paths and node positions; they are
  not stable across edits.

### Edge qualifiers and read contributions

Graph JSON exports each edge's endpoints, occurrence multiplicity (`count`),
`access`, read-contribution fields, relationship qualifiers, and `edge_type`.
The edge type is one of `data`, `iteration`, `predicate`, `binding`, or
`declaration`. Only data, iteration, and predicate edges are dependency edges;
binding and declaration edges describe graph identity and scope declarations.

- `is_callee` and `is_call_argument` identify call relationships; iteration-only
  dependencies are not callees.
  Both may be true when one dependency supplies both roles, as in `action(action)`.
- `is_variable_read` and `is_callable_read` identify possible read relationships.

`read_contribution_count` and `callable_read_count` record how much each edge
contributes to variable-read and callable-read totals, respectively. They are
independent of `count`. An alternative binding or callable output can have its
read flag set while contributing zero: the source occurrence is counted once
through another edge. A zero contribution does not mean the relationship is
absent or less likely at runtime. Both fields feed variable-read metrics; they
do not count call occurrences or resolved call targets.

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
