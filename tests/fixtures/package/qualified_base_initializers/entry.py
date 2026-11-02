import qualified_base_initializers as package
from . import base


class Plain(package.base.Base):
    pass


class Parameterized(package.base.Base[int]):
    pass


class OptionalInitializer:
    if enabled:
        __init__ = unknown_initializer


class Multiple(OptionalInitializer, package.base.Base):
    pass


def main(value):
    return Plain(value), Parameterized(value), Multiple(value)
