__all__ = ["_dotted_private"]

import __all__.extra


def _dotted_private(value):
    return value


def dotted_public(value):
    return value
