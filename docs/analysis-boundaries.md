# Static analysis boundaries

Model possible dependencies within the supported cases. Preserve uncertainty
through the fallbacks below; do not execute Python.

Deeply nested expressions may raise `RecursionError` and abort analysis.
The PoC does not impose a fixed expression-depth limit.

- [Lexical name lookup](#lexical-name-lookup)
- [Discarded expressions](#discarded-expressions)
- [Star imports and `__all__`](#star-imports-and-__all__)
- [Exceptions and returns](#exceptions-and-returns)
- [Decorators](#decorators)
- [Inheritance and member lookup](#inheritance-and-member-lookup)
- [Callable and receiver inference](#callable-and-receiver-inference)
- [Conditions and iteration](#conditions-and-iteration)
- [Containers and unpacking](#containers-and-unpacking)
- [Import resolution](#import-resolution)
- [Calls and argument binding](#calls-and-argument-binding)
- [Generators and suspension](#generators-and-suspension)
- [Mutation and aliases](#mutation-and-aliases)
- [Metric boundaries](#metric-boundaries)

## Lexical name lookup

Class bodies use complete local declarations: class-local names use visible
class bindings and module fallback; free names may capture enclosing function
bindings. Conditional locals retain fallback candidates until a definite local
binding exists. Explicit `global`/`nonlocal` declarations select their owner.
Interpreter-provided module metadata remains unresolved unless bound in source.
Annotation-only declarations affect lookup without binding a value or adding
reads. Method and comprehension bodies skip the class namespace.

Generic declaration expressions retain type-parameter lookup context.
Runtime generic captures in nested functions and comprehensions remain unresolved.
Ordinary locals and annotation hints retain normal lookup.
Class-private identifiers are modeled using their source spelling. Python name
mangling is not connected: `__value` and `_Class__value` remain distinct names
and attributes, even when Python would treat them as the same attribute.
Private spellings in base and derived classes are not separated by mangling.
Ordinary dunder names such as `__class__` remain supported.

## Discarded expressions

Dependencies describe values consumed by represented source operations, not
every Python name lookup. A discarded bare-name expression such as `value`
adds no dependency and does not retain an otherwise unused import. Calls,
attribute accesses, and other represented computations retain their ordinary
dependencies even when their results are discarded.
Discarded bare names, annotation metadata, and `global`/`nonlocal` declarations
do not invalidate literal `__all__`.

## Star imports and `__all__`

Supported:

- One top-level literal list or tuple of strings assigned only to `__all__`,
  with no other recognized references: `__all__ = ["public", "_private"]`.
- An isolated empty literal, `__all__ = []`, imports nothing.
- Annotation-only declarations: `__all__: list[str]` does not bind a value.
- Public module names when no exact export list is available.
- Only direct module-body deletions remove prior possible exports. Deletions
  in other scopes or under branches, loops, `try`, or `with` preserve them;
  conditions and execution paths are not evaluated.
- Propagation of public names and uncertainty through module-level star
  re-exports, unless an exact literal `__all__` supplies the export set.
- Named and star-expanded imports use the same omission rule, including private
  names. A provider's `__all__` makes names importable; consumer uses or supported
  consumer re-exports determine retention.

Not evaluated:

| Example | Why |
| --- | --- |
| `__all__ = select_exports()` | Requires executing a call. |
| `exports = __all__; exports.append("extra")` | Requires tracking aliases and mutations. |
| `configure(__all__)` | Arbitrary code may change the list. |
| `from external_package import *` | External source is unavailable. |

Fallback: include discovered public names and retain an unresolved `module.*`
dependency for uncertain exports. This accepts extra possible edges instead of
silently losing dependencies. External star imports retain only the wildcard.

## Exceptions and returns

Supported:

- Handler conditions depend on represented computations in the `try` body,
  including `await`, eager comprehensions, and eager class bodies. Defining a
  function or generator expression does not include its deferred body; represented
  default expressions and outer iterable computations still contribute.
  Implicit magic-method calls and their exception dependencies are not modeled.
  Extraction nodes do not contribute handler dependencies; operand computations do.
- Handler type expressions follow clause order and depend on exception dispatch.
  Ordinary `except` type checks and bodies exclude earlier handler-body name bindings;
  `except*` checks may use them.
  Body fallthrough guards do not gate dispatch or `finally`. Plain `try`/`finally`
  restores them afterward; handled `try` and `with` do not propagate them outward.
- Direct `return` and `raise` establish an exit.
- Assertion tests gate subsequent operations; handled `try` and `with` contain those guards.
- Returns after a structurally established exit remain source operations, but do not supply callable outputs.
- Try-else suites inherit body fallthrough guards; structurally unreachable else returns do not supply callable outputs.
  Else reads exclude handler writes and use completed body assignments.
- An `if` establishes an exit when both branches exit.
- A structurally established exit in `finally` replaces earlier return outputs.
- A return inside a single `with` with no target or a simple name target,
  when its body passes conservative syntax checks, such as `return 1`.
- Uncertain exits preserve possible return outputs.

Not proven:

| Example | Why |
| --- | --- |
| `with manager: return compute()` | The call may raise; the manager may suppress it. |
| `with manager: return value` | Name lookup may raise; definite assignment is not proved. |
| `with manager as (a, b): return 1` | Target unpacking may raise and be suppressed. |
| `with manager: check(); return 1` | The call may raise before the return; the manager may suppress it. |

Fallback: retain earlier and later possible return outputs. Removing one requires
a structural override; predicting calls or exception suppression could hide a
real dependency.

## Decorators

- Function and class decorators are assumed to preserve declaration identity when they succeed.
- Decorator expressions retain source dependencies; replacement results are not inferred.
- Builtin `classmethod`/`staticmethod` receiver behavior supports builtin names, direct/qualified builtin imports, and local aliases.
  Source-module decorator re-exports use ordinary method receivers.

## Inheritance and member lookup

Supported:

- Source-defined classes and statically named bases, including internal imports.
- Parameterized bases use the unsubscripted class; `__class_getitem__` results are not inferred.
- Multiple-base lookup in declaration order, not full Python MRO.
  An unresolved earlier base stops inherited lookup.
- Class members exclude global/nonlocal writes and generic parameter bindings.
- Guards surrounding a class do not make its completed member bindings conditional.
- Direct and inherited member bindings, including reassignment and deletion,
  subject to the callable-deletion approximation below.
- Receiver types discovered from constructors or annotations.
- Implicit receiver hints require a function or lambda declared in the class and bound as a member.
  Functions installed through aliases may remain untyped.
- Implicit receiver hints use the declaring class; inherited calls do not specialize method bodies.
- Constructor `__init__` uses class-body bindings and ordinary inherited-member lookup.
  Later `__init__` attribute writes and deletions do not update constructor inference.
- Unshadowed, zero-argument built-in `super()` with an unshadowed implicit class
  cell resolves ordinary method calls
  with one statically named base. Class-valued members retain source dependencies,
  but constructor effects and result types are not inferred through `super()`.

Implicit magic-method dispatch (such as `__bool__`, `__len__`, `__add__`, and
`__getitem__`) is not resolved. Written operations retain operand dependencies;
explicit method calls use ordinary lookup. Constructor `__init__` inference above
is supported.

Not evaluated:

| Example | Why |
| --- | --- |
| `class Child(make_base()): ...` | The base class is computed by a call. |
| `super().method()` with multiple bases | Full Python method resolution order is not modeled. |
| `getattr(obj, name)()` | The member name is determined at runtime. |
| `setattr(Class, name, replacement)` | Arbitrary runtime class mutation is not tracked. |
| A custom `__getattribute__`, descriptor, or metaclass | Lookup can execute arbitrary code. |

Fallback: method lookup uses statically discovered candidates in base declaration
order. Conditional definitions, reassignments, and deletions may contribute
candidates, but lookup does not determine all possible method targets or guarantee
a fallback when a candidate is absent. Missing candidates can leave targets
unresolved; known candidates do not also receive a marker for every possible
runtime replacement. These edges do not guarantee Python's runtime selection.

## Callable and receiver inference

Type inference is a limited aid to member resolution. Support is limited to the
forms listed below; combining supported forms does not imply support for every
expression combination. Other forms may remain unresolved while retaining
their ordinary source dependencies.

F-strings and template strings retain interpolation dependencies without inheriting
their operands' callable or receiver identity.

Supported:

- Direct callable aliases: `action = source_function`.
- Builtin callable identity supports direct names, qualified builtin imports, and linear name/import aliases.
  Other builtin value propagation may remain unresolved.
- Constructor results as receiver candidates: `obj = KnownClass()`.
- Named or qualified class return hints on resolved synchronous, non-generator functions,
  including quoted names, callable aliases, and internal imports. Hints retain declaration context.
- Member inference supports named receivers, direct constructor results, and
  the annotation-based indexing of named containers below. Other computed receiver
  expressions retain source dependencies but may remain unresolved.
- Visible binding versions and multiple possible source targets, subject to the
  import rebinding and conditional builtin shadowing approximations below.
- Within a scope, reads use the bindings visible at their read position, even
  when the consuming graph node is created later.
- Eager comprehension reads capture enclosing bindings at their read position;
  generator bodies retain deferred lookup of enclosing bindings.
- Named and qualified annotations as member-resolution hints.
  Prior member writes through the same receiver binding invalidate qualified
  class hints, including writes in sibling branches.
- Class-object hints accept `type[Class]` and qualified/imported aliases of `builtins.type`.
  Class names inside supported container and class-object hints may be quoted.
- Generic type parameters shadow outer annotation names without implying concrete types.
  Body locals and explicit global declarations take precedence in body reads.
- Hints resolve source classes and proven same-module aliases, including nested
  classes. Package `__init__.py` re-exports are supported as public exports;
  ordinary module facades are not followed solely for annotation inference.
  `type` aliases remain opaque; their lazy values are not used for member inference.
  Annotations do not create data reads or independently retain exports.
- Forward annotation hints use final lexical bindings, including enclosing class
  names; local declarations still block outer lookup.
  Class annotations resolve unshadowed `__class__` to their declaring class.
  Local variable annotations do not forward-resolve container or `type` wrapper aliases.
- Annotation hints retain their originating scope and available lookup position through
  aliases, conditional selections, and supported container element extraction;
  a consumer's local names do not reinterpret the original annotation.
- Annotation inference does not distinguish successive definitions or rebindings
  of the same type name; it may use the final visible binding. Ordinary data
  reads still respect source position.
- Element-type hints from built-in `list`/`tuple`, `typing.List`/`Tuple`, and
  `typing`/`collections.abc` `Sequence`/`MutableSequence` support indexed
  extraction rooted in a named container, such as `items[0]` or `items[0][0]`.
  Qualified or computed containers, such as `Registry.items[0]`, may remain
  unresolved; assigning the container to a name enables indexed inference.
  Loop targets, comprehensions, and unpacking retain source
  dependencies but do not infer element types. Tuple element types are pooled,
  not selected by index.
- Indexed element hints support named or qualified source classes,
  `type[Class]`, and nested supported containers. Union element annotations
  are not expanded; direct receiver unions such as `value: A | B` remain supported.
  Starred and slice annotation arguments supply no element hints.
- Annotations as metadata only; imports used solely in annotations are omitted
  unless needed by resolved runtime member dependencies.
- Type annotations do not count as data reads. Annotation-only declarations,
  including `receiver.field: Type` and `receiver[index]: Type`, do not introduce
  reads of bare receiver or index names, target accesses, or synthetic evaluation
  nodes. Existing computations in target expressions retain their ordinary
  representation. Annotated assignments with a value retain the normal
  assignment dependencies.

Not evaluated:

| Example | Why |
| --- | --- |
| `action = registry[key]` | Arbitrary container contents are not reconstructed. |
| `saved = factory(); saved()` | Returned callable identity is not inferred; factory output dependencies remain. |
| `obj = external_factory()` | Its result type is unavailable without further source information. |
| Union or generic return hints; async or generator returns | Call-result type inference supports simple class hints on synchronous, non-generator functions only. |
| `class Box: child: Worker` | Annotation-only hints require an existing binding; unbound fields remain untyped. |
| `obj = manager.__enter__()` | The manager's type does not establish its result type. |
| Values received through `yield`, `yield from`, or `await` | Receiver types and callable identities are not inferred. |
| Conditional shadowing of builtin names at module or class scope | Preserve source dependencies; callable targets may remain known or unresolved. |
| `(Left if flag else Right).run()` | Member targets of computed receivers are not guaranteed; naming the selected receiver is supported. |
| Deleting class or function bindings, including aliases | Later callable and receiver inference may retain known targets or leave them unresolved. |
| Parameter defaults and call arguments | Do not infer parameter types or specialize function bodies. |
| `case KnownClass() as value` | Pattern captures do not infer receiver types or callable identity. |
| `assert isinstance(obj, KnownClass)` | Runtime assertions are not type proofs. |
| `value: "A | B"` or `values: "list[A]"` | Quoted hints support names and attributes only. |

Fallback: retain value and call dependencies, using available type and callable
candidates as hints. Missing hints leave targets unknown; an opaque external
target need not carry an `is_unresolved` flag. Annotations do not prove runtime
types.

## Conditions and iteration

Supported:

- Branch tests and loop/comprehension `for` clauses use condition nodes to gate body operations.
- Later `match` pattern expressions depend on prior case failure.
- Later match clauses exclude earlier case-body bindings; pattern captures and guard writes remain possible.
- Calls inside tests and iterables participate in graph paths through the
  condition node. Callee paths participate only inside the measured node set
  under the first-repeat path definition.
- Conditional bindings from `if`, `and`/`or`, and conditional expressions.
- Conditional operands use completed walrus assignments; subsequent reads retain possible prior bindings.
- Eager `else`/`elif` name reads exclude prior sibling-body bindings; deferred enclosing reads keep final lookup.
- Loop targets and comprehension filters as source dependencies.
- Completed pattern captures replace prior bindings within their case guard and body; later reads retain conservative candidates.
- Completed iteration targets replace prior bindings inside the body; post-loop reads retain the zero-iteration fallback.
- Async iteration as an explicit operation.
- Graph path statistics over these dependencies within the metric boundaries below.

Not evaluated:

| Modeled source | What remains unknown |
| --- | --- |
| `if enabled:`<br>&nbsp;&nbsp;&nbsp;&nbsp;`first()`<br>`else:`<br>&nbsp;&nbsp;&nbsp;&nbsp;`second()` | Both branches are included as equally possible. Both calls depend on the condition node; the model chooses neither branch and assigns no probabilities. |
| `for item in range(100): action(item)` | Execution counts and loop-carried bindings; bodies use source order without iteration feedback. |
| `while ready(): step()` | Results of `ready()`, iteration count, and termination. |
| `break` / `continue` | Exit effects on subsequent dependencies and binding visibility are not inferred. |
| `if flag: ...; if not flag: ...` | Correlations between separate conditions. |

Fallback: keep possible source dependencies. Conditions express gating, not a
complete control-flow model; graph path counts are not execution-path counts.

## Containers and unpacking

Supported:

- Container construction depends on represented source elements; literal
  constants generally have no separate nodes.
- Index and slice reads depend on represented container and index expressions.
- Syntactic slices preserve supported container hints; custom slice result types remain unknown.
  Other indices use pooled element hints, including runtime slice objects.
- Subscript writes retain target and assigned-value dependencies.
- Unpacking uses a shared extraction operation; nested unpacking adds nested operations.
  Loop and comprehension targets depend on an iteration-item extraction operation.
  Extraction retains source dependencies without inferring element identity.

Not evaluated:

| Example | Why |
| --- | --- |
| `action = [first, second][0]` | Literal contents are not evaluated to select one callable. |
| `left, right = make_pair()` | Iteration is not executed to determine individual values. |
| `first, *rest = items` | The size and contents of the remainder are runtime values. |
| `items[index] = value` | The full container state after mutation is not reconstructed. |

Fallback: preserve dependencies on the source container, access expressions,
and assigned values. Sharing a source dependency does not prove that extracted
values have the container's type, identity, or callable targets.

## Import resolution

Supported:

- Absolute and relative imports under the selected source tree's module naming;
  this does not reproduce Python's environment-dependent import search.
  Relative imports above the top-level package retain an unresolved relative prefix.
- Source layouts with duplicate module names (such as `same.py` alongside
  `same/__init__.py`) are rejected with both source paths in the diagnostic.
- Discovery skips descendant directories named `.git`, `.idea`, `.mypy_cache`,
  `.nox`, `.pytest_cache`, `.ruff_cache`, `.venv`, `__pycache__`, `env`,
  `node_modules`, or `venv` before inspecting their files. This list is fixed;
  `.gitignore` does not control discovery. The selected source directory itself
  is scanned even if its name is in this list. Use `source` (CLI: `--source`)
  to select a narrower source tree; other excluded descendants remain skipped.
- Reject symlinked Python files among discovered sources and explicit file
  targets. Discovery
  does not recurse into symlinked directories or detect other filesystem aliases.
  Sources outside the selected source tree remain prohibited.
- Import aliases and source re-exports. Callable/member inference assumes one
  binding for the imported local name in its scope. Reimports or assignment
  rebindings may retain known targets or leave them unresolved; ordinary source
  reads still respect binding positions. Imports in separate scopes and
  `__init__.py` re-exports remain supported.
- Class-body imports support lexical uses; class-attribute access alone may not retain or resolve them.
- Initializer submodule re-exports preserve module identity; assigned members can shadow it.
  Aliased dotted imports follow discovered parent modules; intermediate package-object replacements are not inferred.
- Module identity follows imports and linear name aliases. Saving a module attribute as an alias preserves its dependency but may leave later member lookup unresolved.
- Internal imported values and calls connected to discovered source targets.
- Linear callable aliases and re-exports preserve distinct source declarations and known outputs.
- Statically named ordinary external imports and qualified calls represented by
  shared named targets; external star imports use wildcard dependencies.
- External qualified calls through direct imports and linear module-alias chains.
  Saving an external attribute as a value does not infer its callable identity.
  Conditional module selections retain operand and call dependencies, but
  qualified member targets are outside this inference boundary. Conditional
  selections at the call site can resolve known source callables.
- Omission of unused imports and annotation-only dependencies, with retention
  where needed for exports or resolved members. Uses refer to lexical bindings,
  not matching names in unrelated scopes; import side effects are not inferred.

Runtime import behavior not predicted:

| Example | Why |
| --- | --- |
| `importlib.import_module(module_name)` | The module name is a runtime value. |
| `sys.path.insert(0, location)` | Filesystem discovery uses the selected source tree. |
| `sys.modules["api"] = replacement` | Runtime module replacement is not tracked. |
| Import cycles and partial initialization | Provider names use final visible bindings; import-time snapshots are not modeled. |
| Conditional callable selections exported across modules | Retain operand dependencies; callable targets need not be fully enumerated. |
| `external_api.run()` | The call is modeled, but external implementation is unavailable. |
| `(first if flag else second).run()` | Selecting an external module does not establish a qualified member target. |

Fallback: retain calls and available import dependencies without loading modules
or executing their initialization. Named external targets identify dependencies;
they do not establish that an import succeeds or predict its effects.

## Calls and argument binding

Supported:

- Represented callable and argument expressions as dependencies of each call;
  literal constants need not have separate nodes.
- Resolved source outputs as dependencies of the call, or the source scope when
  it has no outputs.
- Parameters as bindings inside the function body.
- Default-expression dependencies recorded at the declaration, without evaluation.

Arguments feed the call; parameters feed the function's internal operations.
Path metrics count these graph dependencies without mapping arguments to
parameters or expanding individual invocations.

Not evaluated:

| Example | Why |
| --- | --- |
| `process(*items, **options)` | Contents are not expanded to match the function signature. |
| `invoke(callback)` with `callback()` in its body | The argument is modeled, but the body is not specialized for each supplied callback. |
| A closure called before a later enclosing reassignment | Deferred enclosing reads use final visible bindings, without invocation-time versions. |
| `process(unexpected=value)` | Signature validity and runtime `TypeError` are not proved. |

Fallback: retain call, argument, and available callee dependencies. Function
bodies are modeled once, without simulating individual invocations.

## Generators and suspension

Supported:

- Separate nodes for a yielded output and the value received on resumption.
- `yield from` outputs and expression results linked to the delegated source.
- `await` expressions as dependencies within their source scope.
- Async iteration as an operation feeding its loop target.
- Generator-expression dependencies even when consumption is unknown.
- Async generator expressions initialize their outer async iterator in the enclosing scope; inner clauses remain deferred.

Not evaluated:

| Example | Why |
| --- | --- |
| `generator.send(value)` | The supplied value is not mapped to a particular suspended `yield`. |
| `next(generator)` | The current suspension point and number of resumptions are not tracked. |
| `await task` | Scheduling, completion order, and cancellation are runtime behavior. |
| `pending = (action(item) for item in items)` | The graph includes the body without proving whether or when it is consumed. |

Fallback: retain source dependencies without simulating suspension or scheduling.
A value received by `yield` has a separate result node with no incoming value
dependency, rather than an `is_unresolved` placeholder. It is not assumed to be
the yielded value.

## Mutation and aliases

Supported:

- Explicit attribute and subscript writes with receiver and value dependencies.
- Augmented assignments with dependencies on the previous value and operand.
- Explicit name deletions and their effects on visible bindings, except that
  callable and receiver inference after deleting class or function bindings is
  outside the boundary. Deletions remain source operations; attribute and
  subscript deletions are write references, not reconstructed heap changes.
- Guarded deletions preserve prior possible bindings, matching export discovery;
  this does not require modeling whether a guard executes.
- Deletion cannot invalidate bindings from the opposite `if` arm.
- Interrupted execution and context-manager suppression preserve possible assignment bindings.
  In-body reads use completed assignments; definite later assignments replace earlier candidates.
- Enclosing walrus writes in comprehensions nested under branches may retain prior values in body reads.
- Deletions under `try`/`with` retain prior candidates; exact visibility is not inferred.
- Global/nonlocal `del` statements remain source operations, but do not change
  binding visibility or export discovery in other scopes.
- Class-body `global`/`nonlocal` writes remain source operations with their
  declared owner, but do not publish bindings for reads or exports in other
  scopes, including reads after the class.
- Writes through function parameters recorded inside the function scope.

Not evaluated:

| Example | Why |
| --- | --- |
| `alias = obj; alias.field = value` | The write is modeled, but a shared heap state for `alias` and `obj` is not maintained. |
| `items[index].member = value` or `factory().member = value` | Receiver identity is not tracked; member hints may remain. |
| `Class.member = replacement` | Only lookups through the same receiver binding in the same scope are invalidated; aliases and instances are not updated. |
| `update(obj)` | The call is modeled; callee mutations are not propagated back to the caller's object. |
| `items.append(value)` | The method call is modeled without reconstructing the resulting container contents. |
| `obj.field = value` with a custom setter | The assignment is modeled without executing descriptor behavior. |

Fallback: retain explicit write and call dependencies. An alias dependency does
not establish a complete model of shared object state or all indirect effects.

## Metric boundaries

Supported:

- Direct profiles measure one scope's nodes; aggregate profiles measure the
  scope and its descendants together. Paths exclude dependencies outside that set.
- Path traversal follows data, iteration, and predicate dependencies, excluding
  binding and declaration edges and binding nodes.
- Callable scopes contribute zero-depth endpoints only when their scopes are selected.
- Each dependency endpoint is visited once per consuming node; repeated edge
  occurrences do not multiply paths.
- Cyclic nodes and their dependencies remain in path measurement. Each path
  stops on its first repeated node, counting the closing edge in length.
  Visited nodes are tracked per path, not globally.
- Exact cyclic counting has deterministic state and work limits documented in
  [metrics](metrics.md). Exceeding them makes affected path metrics unavailable
  (`null`), without reporting partial counts. Other metrics remain available.
- Component and cyclic-node counters include binding nodes; paths exclude them.
- `graph.paths.data.count_sum` sums path counts at named endpoints, including
  intermediate values; shared prefixes contribute at each endpoint.
- `graph.paths.expressions.count` sums paths at sinks and every member of
  terminal cyclic components (those without an outside consumer).
- A root has one path at depth zero. Each edge adds one to depth; incoming path
  distributions are added. Depth p95 uses nearest rank.

Not evaluated:

| Example | Why |
| --- | --- |
| A direct caller profile referencing another function's output | The callee's nodes are outside the measured scope. |
| Unbounded walks through cycles | Paths stop at their first repeated node. |
| Multiple edge types connecting the same dependency to one consumer | They identify one dependency endpoint for path traversal. |
| Adding direct-scope path counts to obtain an aggregate | Cross-scope dependencies and cycles require recomputing the combined graph. |

Interpret counts and depths within the measured scope boundary and alongside
cyclic-region size. Path counts are structural measurements, not execution counts
or code-quality scores. See [metric definitions](metrics.md).
