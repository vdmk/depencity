from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from depencity._graph.model.ir import BindingEnvironment, ScopeRecord


@dataclass(frozen=True, eq=False)
class Reference:
    """An expression identity, or a name read with its lexical lookup point."""

    description: str
    read_scope: 'ScopeRecord | None' = field(default=None, repr=False)
    read_position: int | None = None
    environment: 'BindingEnvironment | None' = field(default=None, repr=False)
