__all__ = ["export"]


try:
    raise RuntimeError
except RuntimeError as __all__:
    pass


def export(value):
    return value
