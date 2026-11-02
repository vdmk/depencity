from external_api import configure

__all__ = ["_subscript_private"]
__all__[configure(__all__)]: int


def _subscript_private(value):
    return value


def subscript_public(value):
    return value
