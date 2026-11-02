from ..worker import transform


def main(value):
    return transform(value)


def beyond_package(value):
    from ...relative_imports import transform
    return transform(value)
