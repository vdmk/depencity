__all__ = ["_aliased_private"]

import __all__.extra as api


def _aliased_private(value):
    return value


def aliased_public(value):
    return value
