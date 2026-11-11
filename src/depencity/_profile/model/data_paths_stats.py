from dataclasses import dataclass, field


@dataclass(frozen=True)
class DataPathsStats:
    """Exact path statistics; None marks metrics exceeding cyclic counting limits."""

    expression_paths: int | None = 0
    expression_depth_max: int | None = 0
    count: int | None = 0
    depth_max: int | None = 0
    depth_mean: float | None = 0.0
    depth_p95: int | None = 0
    depth_distribution: dict[int, int] | None = field(default_factory=dict)
