from external import Public

__all__ = ["Public"]

field: tuple[__all__] = None


def helper(value: tuple[__all__]) -> tuple[__all__]:
    return value


async def async_helper(value: tuple[__all__]) -> tuple[__all__]:
    local: tuple[__all__] = value
    return local


class Container:
    field: tuple[__all__] = None
