from dataclasses import dataclass, field


@dataclass(frozen=True)
class DataPathsStats:
    """Measured expression-sink and named-node path statistics for one scope."""

    expression_paths: int = 0
    expression_depth_max: int = 0
    count: int = 0
    depth_max: int = 0
    depth_mean: float = 0.0
    depth_p95: int = 0
    depth_distribution: dict[int, int] = field(default_factory=dict)
