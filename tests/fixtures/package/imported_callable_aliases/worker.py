def work():
    return 1


class A:
    @staticmethod
    def run():
        return payload_a


class B:
    @staticmethod
    def run():
        return payload_b


class Nested:
    class A:
        @staticmethod
        def run():
            return nested_payload_a

    class B:
        @staticmethod
        def run():
            return nested_payload_b


class Repeated:
    @staticmethod
    def run():
        return earlier_payload

    earlier = run

    @staticmethod
    def run():
        return later_payload

    later = run


first = A.run
second = B.run
nested_first = Nested.A.run
nested_second = Nested.B.run
earlier = Repeated.earlier
later = Repeated.later


native_length = len


def provide_length():
    return len


from builtins import staticmethod as static
from builtins import classmethod as class_method


from unavailable_library import external_choice
mixed_action = work if enabled else external_choice
external_alias = external_choice


from builtins import len as imported_length


from unavailable_library import initialize


class ExternalInitializer:
    __init__ = initialize


def same_module_targets():
    from . import worker as self_module

    return self_module.work(), self_module.A()
