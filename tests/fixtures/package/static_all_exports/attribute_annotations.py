from external_api import configure

__all__ = ["_attribute_private"]
configure(__all__).value: int


def _attribute_private(value):
    return value


def attribute_public(value):
    return value
