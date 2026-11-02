__all__ = ["_visible", "explicitly_removed"]


def _visible():
    return 1


def explicitly_removed():
    return 2


del explicitly_removed
