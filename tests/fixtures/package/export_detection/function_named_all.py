__all__ = ["export"]


@export
def __all__(
    value=lambda item=export, other=export, *, required: item,
    other=export,
    *,
    required,
):
    return value


def export(value):
    return value
