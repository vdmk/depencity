__all__ = ["_work"]


def _work(value):
    return value


def inspect_exports():
    return __all__


def local_shadow():
    __all__ = ["_local_only"]
    return __all__
