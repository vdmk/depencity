from .worker import run
from .worker import run as Imported
from .worker import value
from .middle import Alias as Middle

Assigned = run
Long = Middle
Value = value
Container = [run]
Computed = build(run)
