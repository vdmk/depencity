__all__ = ["export"]
other = ["other"]
other[0] = "changed"
value = __all__[0]
__all__[0] = "changed"


def export(value):
    return value
