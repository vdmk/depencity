from dataclasses import dataclass as conditional_dataclass


def decorate(function):
    def wrapper(value):
        return other

    return wrapper


def keep(function):
    return function


keep_alias = keep


@keep_alias
def alias_decorated(value):
    return original


@keep_alias
class AliasDecorated:
    def run(self):
        return original


def rebound_decorator(function):
    return function


rebound_decorator = keep


@rebound_decorator
def rebound_decorated(value):
    return original


def wrap_inner(function):
    def inner(value):
        return function(value)

    return inner


def wrap_outer(function):
    def outer(value):
        return function(value)

    return outer


@decorate
def transformed(value):
    return original


@keep
def unchanged(value):
    return value


@wrap_outer
@wrap_inner
def stacked(value):
    return original


@unknown_decorator
def uncertain(value):
    return original


def make_decorator(value):
    return unknown_decorator


@make_decorator('option')
def factory_decorated(value):
    return original


def generate_identity(function):
    yield function
    return function


def generate_wrapper(function):
    def wrapper(value):
        return other

    yield wrapper
    return wrapper


@generate_identity
def generator_decorated(value):
    return original


@generate_wrapper
def generator_wrapped(value):
    return original


async def decorate_async(function):
    return function


async def wrap_async(function):
    def wrapper(value):
        return other

    return wrapper


@decorate_async
def coroutine_decorated(value):
    return original


@wrap_async
class CoroutineDecorated:
    def run(self):
        return original


@keep
async def kept_async(value):
    return value


def conditional_decorator(function):
    return function


if replace_decorator:
    conditional_decorator = unknown_decorator


@conditional_decorator
def conditionally_decorated(value):
    return original


if replace_decorator:
    conditional_dataclass = unknown_decorator


@conditional_dataclass
class ConditionallyDecorated:
    def run(self):
        return original


def keep_before_default(function):
    return function


@keep_before_default
def default_rebinds_decorator(
    value=(keep_before_default := unknown_decorator), later=keep_before_default
):
    return value


unknown_before_default = unknown_decorator


@unknown_before_default
def default_introduces_decorator(value=(unknown_before_default := keep)):
    return value


def keep_before_keyword(cls):
    return cls


@keep_before_keyword
class KeywordRebindsDecorator(metaclass=(keep_before_keyword := type)):
    def run(self):
        return original


def main(value):
    return (
        alias_decorated(value),
        AliasDecorated().run(),
        rebound_decorated(value),
        keep_alias(value),
        transformed(value),
        unchanged(value),
        stacked(value),
        uncertain(value),
        factory_decorated(value),
        generator_decorated(value),
        generator_wrapped(value),
        coroutine_decorated(value),
        CoroutineDecorated(),
        kept_async(value),
        conditionally_decorated(value),
        ConditionallyDecorated().run(),
        default_rebinds_decorator(value),
        default_introduces_decorator(value),
        KeywordRebindsDecorator().run(),
    )


@unknown_decorator
def opaque_with_default(value=len):
    return original


def call_opaque_default():
    alias = opaque_with_default
    return opaque_with_default(), alias()


import builtins as standard
from builtins import classmethod as ClassMethod, staticmethod as StaticMethod


class ImportedDecorators:
    VALUE = receiver_payload

    @ClassMethod
    def create(cls):
        return cls()

    @standard.classmethod
    def qualified_create(cls):
        return cls()

    @StaticMethod
    def read(value):
        return value.VALUE

    @standard.staticmethod
    def qualified_read(value):
        return value.VALUE


def shadow_imported_decorator():
    ClassMethod = custom_decorator

    class Local:
        @ClassMethod
        def create(cls):
            return cls()

    return Local.create()


class CapturedDecorator:
    @standard.classmethod
    @configure(standard := replacement)
    def create(cls):
        return cls()


class LayeredDescriptors:
    @ClassMethod
    @StaticMethod
    def class_over_static(cls):
        return cls()

    @StaticMethod
    @ClassMethod
    def static_over_class(cls):
        return cls()


def layered_method_values():
    first = LayeredDescriptors.class_over_static
    second = LayeredDescriptors.static_over_class
    return first, second


namespace = standard
chained_namespace = namespace


class NamespaceDecorators:
    @chained_namespace.classmethod
    def create(cls):
        return cls()

    @chained_namespace.staticmethod
    def read(value):
        return value.VALUE


assigned_classmethod = ClassMethod
assigned_staticmethod = StaticMethod


class AssignedDecorators:
    @assigned_classmethod
    def create(cls):
        return cls()

    @assigned_staticmethod
    def read(value):
        return value.VALUE


native_classmethod = classmethod
native_staticmethod = staticmethod


class NativeDecorators:
    @native_classmethod
    def create(cls):
        return cls()

    @native_staticmethod
    def read(value):
        return value.VALUE


@keep
class Initialized:
    def __init__(self, value):
        initialize(value)


def constructor_inputs(value):
    direct = Initialized(value)
    shared = Initialized(Initialized)
    return direct, shared


def hinted_constructor(factory: type[Initialized]):
    return factory(Initialized)
