# Compare a refactoring

See [profile interpretation](interpreting-profiles.md) for scope aggregation,
own profiles, depth, and metric interpretation.

Use the same analyzer version, target scope, and options for each measurement.
This small example removes intermediate bindings while preserving addition
before multiplication. Download [before](refactoring-examples/refactoring-before.py)
and [after](refactoring-examples/refactoring-after.py) into the same directory.

Before:

```python
def compute(left, right):
    total = left + right
    total = total * 2
    return total
```

After:

```python
def compute(left, right):
    return (left + right) * 2
```

With Depencity 0.1.0 installed, run:

```bash
depencity profile refactoring-before.py --depth 2 --include-own-profile
depencity profile refactoring-after.py --depth 2 --include-own-profile
```

The graph has three scopes in both versions. The remaining measurements in
the table are the same for `compute` and the whole graph.

<!-- refactoring-table:start -->
| Measurement | Before | After |
| --- | ---: | ---: |
| Total scopes (root, module, function) | 3 | 3 |
| Variable reads | 4 | 2 |
| Variable writes | 4 | 2 |
| Expression path count | 2 | 2 |
| Maximum expression path length | 5 | 3 |
| Data path count | 8 | 4 |
| Maximum data path length | 5 | 3 |
| Mean data path length | 2.75 | 1.5 |
| Data path length p95 | 5 | 3 |
| Version merges | 0 | 0 |
| Cyclic components | 0 | 0 |
<!-- refactoring-table:end -->

The [before graph](refactoring-examples/refactoring-before.svg) and
[after graph](refactoring-examples/refactoring-after.svg) retain both arithmetic
operations. Removing the two assignments to `total` removes two reads, two writes,
and two edges from the longest chain. Data path counts also fall because
intermediate named endpoints are gone. The scope count stays the same, and neither graph contains a cycle.

For this short expression, the direct return remains readable. In a larger
expression, an intermediate name may explain intent and be worth retaining.
These measurements support that review; they do not establish a universal
preference for fewer variables or prove improved maintainability.

Validate behavior separately. In a checkout, this command checks all 1,681
integer input pairs from -20 through 20:

```bash
uv run python - <<'PY'
import runpy
before = runpy.run_path("docs/refactoring-examples/refactoring-before.py")["compute"]
after = runpy.run_path("docs/refactoring-examples/refactoring-after.py")["compute"]
for left in range(-20, 21):
    for right in range(-20, 21):
        assert before(left, right) == after(left, right)
PY
```

Finite checks are not a proof for arbitrary objects with overloaded operators.
For real changes, run the project's existing behavior checks and inspect
[metric boundaries](analysis-boundaries.md#metric-boundaries) before interpreting
counter changes. Cross-scope paths must be recomputed together, rather than
adding individual scope profiles.
