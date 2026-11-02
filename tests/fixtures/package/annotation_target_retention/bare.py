from .facade import Bare, Index, Position

Bare.field: int
Bare[Index]: int
Bare[Index:Index:Index]: int
Bare[0]: int
Bare[Position()]: int
Bare[Index:Position()]: int
