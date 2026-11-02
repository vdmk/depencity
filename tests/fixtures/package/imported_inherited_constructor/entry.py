from .cycle_a import A
from .worker import Base, ComputedBase, Conditional, Imported, GlobalInitializer, AliasedInitializer, LaterInitializer
from .middle import B
from .base import Empty, HasInitializer


class Local(Base):
    pass


class Deep(Local):
    pass


class Override(Base):
    def __init__(self, value):
        self.value = value


class Shadowed(Base):
    __init__ = unknown


class Deleted(B):
    def __init__(self, value):
        self.value = value

    del __init__


class DeepImported(B):
    pass


class MultipleBases(Empty, HasInitializer):
    pass


class ConditionalDeleted(Base):
    def __init__(self, value):
        self.value = value

    if enabled:
        del __init__


def callback(value):
    return value


def main(value):
    return (
        Imported(value),
        A(value),
        Local(value),
        Deep(value),
        Override(value),
        Shadowed(value),
        Deleted(value),
        DeepImported(value),
        B(value),
        MultipleBases(value),
        ConditionalDeleted(value),
        callback(Local),
    )


def invoke_method(value: Conditional):
    return value.method()


def create_conditional():
    return Conditional()


def nested_class(value):
    class Nested(Base):
        pass

    return Nested(value)


def read_cyclic_member(value: A):
    return value.missing


def create_computed_base(value):
    return ComputedBase(value)


def global_initializer(value):
    return GlobalInitializer(value)


def aliased_initializer(value):
    return AliasedInitializer(value)


def later_initializer(value):
    return LaterInitializer(value)


def replaced_initializer(value, replacement):
    Imported.__init__ = replacement
    return Imported(value), Imported.__init__(value)


def deleted_initializer(value):
    del Imported.__init__
    return Imported(value), Imported.__init__(value)


def assigned_factory_alias(value):
    factory = AliasedInitializer
    return factory(value)


def initializer_argument():
    factory = AliasedInitializer
    return factory(AliasedInitializer.__init__)


class LocalFallback:
    def __init__(self, value):
        self.value = fallback_value

    def method(self):
        return fallback_method


class OrderedConstructor(Base, LocalFallback):
    pass


class OrderedMethods(Conditional, LocalFallback):
    pass


def construct_ordered_bases(value):
    return OrderedConstructor(value)


def call_ordered_method(value):
    return OrderedMethods(value).method()


class OpaqueFirst(unknown_base, LocalFallback):
    pass


def construct_opaque_base(value):
    return OpaqueFirst(value)


def call_opaque_base(value):
    return OpaqueFirst(value).method()


class IndirectFirst(Base):
    pass


class IndirectOrder(IndirectFirst, LocalFallback):
    pass


def construct_indirect_order(value):
    return IndirectOrder(value)


class IndirectOpaque(OpaqueFirst, LocalFallback):
    pass


def construct_indirect_opaque(value):
    return IndirectOpaque(value)
