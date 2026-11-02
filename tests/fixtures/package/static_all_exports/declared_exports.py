global __all__
__all__ = ["_declared_private"]


def _declared_private(value):
    return value


def declare_exports():
    global __all__
