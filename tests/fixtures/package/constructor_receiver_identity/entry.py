from .worker import C as ImportedC
from .worker import D as ImportedD
from .worker import Derived as ImportedDerived


class C:
    def method(self):
        return 'entry C'


class Reused:
    def method(self):
        return 'first Reused'


def repeated_definition():
    value = Reused()
    return value.method()


class Reused:
    def method(self):
        return 'last Reused'


def parameter_shadow(C):
    value = C()
    return value.method()


def local_import_shadow():
    from .worker import C
    C = unknown
    value = C()
    return value.method()


def non_class_factory():
    from .worker import make_value as C
    value = C()
    return value.method()


def class_alias_chain():
    first = ImportedC
    second = first
    value = second()
    return value.method()


def unknown_class_rebind(unknown_class):
    alias = ImportedC
    alias = unknown_class
    value = alias()
    return value.method()


def missing_class_member():
    alias = ImportedC
    value = alias()
    return value.missing()


def inherited_class_alias():
    alias = ImportedDerived
    value = alias()
    return value.method()


def conditional_classes(flag):
    value = ImportedC()
    if flag:
        value = ImportedD()
    return value.method()


def replace_member(replacement):
    value = ImportedC()
    value.method = replacement
    return value.method()


def delete_member():
    value = ImportedC()
    del value.method
    return value.method()


def call_before_write(replacement):
    value = ImportedC()
    before = value.method()
    value.method = replacement
    return before, value.method()


def rebind_after_write(replacement):
    value = ImportedC()
    value.method = replacement
    value = ImportedC()
    return value.method()


def write_other_member(replacement):
    value = ImportedC()
    value.other = replacement
    return value.method()


def accept_class_default(value=ImportedC):
    return value


def call_with_class_default():
    return accept_class_default()


def unpack_class():
    action, other = ImportedC
    return action()


def iterate_class():
    for action in ImportedC:
        return action()


def comprehend_class():
    return [action() for action in ImportedC]


def main(flag):
    return (
        repeated_definition(),
        ImportedC().method(),
        parameter_shadow(unknown),
        local_import_shadow(),
        non_class_factory(),
        conditional_classes(flag),
    )
