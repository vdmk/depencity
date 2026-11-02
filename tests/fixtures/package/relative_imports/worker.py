def transform(value):
    return value + 1


def _beyond_package(value):
    from ..relative_imports import transform
    return transform(value)


def _beyond_package_symbol(value):
    from .. import transform
    return transform(value)
