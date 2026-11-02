"""Keep pytest assertion reports bounded for large snapshot structures."""


def pytest_assertrepr_compare(config, op, left, right):
    if op != '==' or not _is_large_structure(left) or not _is_large_structure(right):
        return None
    left_keys = set(left) if isinstance(left, dict) else None
    right_keys = set(right) if isinstance(right, dict) else None
    lines = [
        'large structure comparison failed',
        f'left: {_shape(left)}',
        f'right: {_shape(right)}',
    ]
    if left_keys is not None and right_keys is not None:
        lines.append(f'keys only on left: {sorted(left_keys - right_keys)!r}')
        lines.append(f'keys only on right: {sorted(right_keys - left_keys)!r}')
    return lines


def _is_large_structure(value) -> bool:
    return _bounded_size(value) > 10_000


def _bounded_size(value, limit=100_001) -> int:
    if limit <= 0:
        return limit
    if isinstance(value, dict):
        return min(limit, 2 + sum(
            _bounded_size(key, limit) + _bounded_size(item, limit)
            for key, item in value.items()
        ))
    if isinstance(value, (list, tuple, set, frozenset)):
        return min(limit, 2 + sum(_bounded_size(item, limit) for item in value))
    if isinstance(value, str):
        return min(limit, len(value))
    return 1


def _shape(value):
    if isinstance(value, dict):
        return f'dict({len(value)} keys)'
    if isinstance(value, (list, tuple, set, frozenset)):
        return f'{type(value).__name__}({len(value)} items)'
    return type(value).__name__
