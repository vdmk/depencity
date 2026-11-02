class A:
    def run(self):
        return 1


class B(A):
    def run(self):
        return 2

    def accept(self, value):
        return value


class C(B):
    def explicit(self):
        return super(B, self).run()

    def zero_argument(self):
        return super().run()

    def saved_alias(self):
        saved = super().run
        alias = saved
        return alias()

    def dynamic(self, starting_class):
        return super(starting_class, self).run()

    def rebind_global_in_argument(self, replacement):
        global super
        return super().accept(super := replacement)


@unknown_decorator
class DecoratedChild(B):
    def run(self):
        return super().run()


def replace_class(cls):
    return B


@replace_class
class ReplacedChild(B):
    def run(self):
        return super().run()


def main():
    return DecoratedChild(), ReplacedChild()


class ParentProxy(A):
    def parent_proxy(self):
        return super()


class Fields:
    value = field_payload

    def method(self):
        return method_payload


class ReadFields(Fields):
    def read_value(self):
        return super().value

    def read_method(self):
        return super().method


class NestedProxy(A):
    def outer(self):
        def inner(receiver):
            return super().run()

        return inner(self)

    def shadowed_cell(self):
        def inner(receiver):
            __class__ = replacement
            return super().run()

        return inner(self)
