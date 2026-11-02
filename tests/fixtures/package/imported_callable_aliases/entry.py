from .worker import work
from .worker import first, second, nested_first, nested_second, earlier, later
from unavailable_library import external_work


def main():
    alias = work
    return alias()


def distinct_methods():
    f = first
    g = second
    f()
    g()


def nested_methods():
    f = nested_first
    g = nested_second
    f()
    g()


def repeated_methods():
    f = earlier
    g = later
    f()
    g()


def argument_control():
    return unknown(first, second)


def alias_chain():
    first = work
    second = first
    return second()


def unknown_rebind():
    alias = work
    alias = unknown_callable
    return alias()


def external_alias():
    alias = external_work
    return alias()


def argument_only():
    return consume(work)


def captured(other):
    alias = work
    return alias(alias := other)


def captured_reverse(other):
    alias = other
    return alias(alias := work)


def captured_external(other):
    alias = external_work
    return alias(alias := other)


def local_import():
    from .worker import work
    alias = work
    return alias()


def unpacked():
    alias, other = work
    return alias()


def iterated():
    for alias in work:
        return alias()


def unpacked_external():
    alias, other = external_work
    return alias()


def iterated_external():
    for alias in external_work:
        return alias()


def accept_internal_default(value=work):
    return value


def accept_external_default(value=external_work):
    return value


@external_work
def decorated():
    return 1


def call_declarations():
    internal_alias = accept_internal_default
    external_alias = accept_external_default
    decorated_alias = decorated
    return (
        accept_internal_default(),
        accept_external_default(),
        decorated(),
        internal_alias(),
        external_alias(),
        decorated_alias(),
    )


def select_callables(flag):
    selected = work if flag else external_work
    return (
        selected(),
        (work if flag else external_work)(),
        (work or external_work)(),
        (external_work if work else unknown_callable)(),
        (work + external_work)(),
        unknown_factory()(work, external_work),
    )


def select_with_member_test(config):
    return (work if config.enabled else external_work)()


def imported_builtin(values):
    from .worker import native_length

    return native_length(values)


def aliased_imported_builtin(values):
    from .worker import native_length

    saved = native_length
    return saved(values)


def builtin_argument():
    from .worker import native_length

    return unknown(native_length)


def returned_builtin(values):
    from .worker import provide_length

    return provide_length()(values)


from .worker import static, class_method
from builtins import staticmethod as NativeStatic
from builtins import classmethod as NativeClassMethod


class DecoratedWorker:
    def run(self):
        return receiver_payload

    @static
    def reexported_static(value):
        return value.run()

    @NativeStatic
    def direct_static(value):
        return value.run()

    @class_method
    def reexported_class(cls):
        return cls()

    @NativeClassMethod
    def direct_class(cls):
        return cls()


def mixed_imported_action():
    from .worker import mixed_action

    return mixed_action()


def mixed_imported_alias():
    from .worker import mixed_action

    saved = mixed_action
    return saved()


def external_reexport():
    from .worker import external_alias

    return external_alias()


def qualified_mixed_action():
    from . import worker

    return worker.mixed_action()


def imported_builtin_reexport(values):
    from .worker import imported_length

    return imported_length(values)


def builtin_reexport_argument():
    from .worker import imported_length

    return unknown(imported_length)


def external_reexport_alias():
    from .worker import external_alias

    saved = external_alias
    return saved()


def external_identity():
    from .worker import external_alias
    from unavailable_library import external_choice

    external_alias()
    external_choice()


def imported_initializer():
    from .worker import ExternalInitializer

    return ExternalInitializer()


def mixed_imported_constructor(flag):
    from .worker import A

    factory = A if flag else external_work
    instance = factory()
    return instance.run()


def mixed_constructor_expression(flag):
    from .worker import A

    instance = (A if flag else external_work)()
    return instance.run()
