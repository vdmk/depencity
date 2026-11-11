from dataclasses import dataclass, field


@dataclass
class ScopeProfile:
    """Measured dependency metrics for one scope or an aggregate subtree."""

    variable__local__read__count: int = 0
    variable__enclosing__read__count: int = 0
    variable__module__read__count: int = 0
    variable__builtin__read__count: int = 0
    variable__other_scope__read__count: int = 0
    variable__unresolved__read__count: int = 0
    variable__total__read__count: int = 0
    variable__total__read__distinct_count: int = 0
    variable__local__write__count: int = 0
    variable__enclosing__write__count: int = 0
    variable__module__write__count: int = 0
    variable__total__write__count: int = 0
    attribute__total__read__count: int = 0
    attribute__total__write__count: int = 0
    attribute__class__read__count: int = 0
    attribute__class__write__count: int = 0
    attribute__external__read__count: int = 0
    attribute__external__write__count: int = 0
    subscript__read__count: int = 0
    subscript__write__count: int = 0
    call__occurrences__total__count: int = 0
    call__occurrences__resolved__count: int = 0
    call__occurrences__unresolved__count: int = 0
    call__dependencies__resolved_targets__count: int = 0
    call__dependencies__external__count: int = 0
    call__dependencies__external__distinct_count: int = 0
    construction__container_creation__count: int = 0
    graph__paths__expressions__count: int = 0
    graph__paths__expressions__length__max: int = 0
    graph__paths__data__count_sum: int = 0
    graph__paths__data__length__max: int = 0
    graph__paths__data__length__mean: float = 0.0
    graph__paths__data__length__p95: int = 0
    graph__paths__data__length__distribution: dict[int, int] = field(default_factory=dict)
    graph__version_merges__count: int = 0
    graph__cyclic_components__count: int = 0
    graph__cyclic_components__nodes__count: int = 0
