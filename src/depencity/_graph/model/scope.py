from collections.abc import Iterator
from dataclasses import dataclass, field

from depencity._graph.model.enums import ScopeKind
from depencity._graph.model.node import Node


@dataclass(eq=False)
class Scope:
    """A lexical graph container that owns nodes and child scopes."""

    name: str
    kind: ScopeKind
    parent: Scope | None
    children: list[Scope] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    is_standalone_module: bool = False

    def walk_scopes(self) -> Iterator[Scope]:
        """Yield this scope and its descendants in declaration order."""
        pending = [self]
        while pending:
            scope = pending.pop()
            yield scope
            pending.extend(reversed(scope.children))

    def path(self) -> str:
        if (
            self.parent is None
            or self.parent.kind == ScopeKind.ROOT
            or self.parent.is_standalone_module
        ):
            return self.name
        return f"{self.parent.path()}.{self.name}"


def create_scope_ids(scopes: list[Scope]) -> dict[int, str]:
    """Allocate collision-free display identifiers in scope traversal order."""
    counts: dict[str, int] = {}
    used_ids: set[str] = set()
    result: dict[int, str] = {}
    for scope in scopes:
        base = scope.path()
        occurrence = counts.get(base, 0) + 1
        candidate = base if occurrence == 1 else f'{base}#{occurrence}'
        candidate = create_unique_id(candidate, used_ids)
        counts[base] = occurrence
        used_ids.add(candidate)
        result[id(scope)] = candidate
    return result


def create_unique_id(candidate: str, used_ids: set[str]) -> str:
    """Select an unused identifier without changing the supplied identifier set."""
    if candidate not in used_ids:
        return candidate
    suffix = 2
    while f'{candidate}#{suffix}' in used_ids:
        suffix += 1
    return f'{candidate}#{suffix}'
