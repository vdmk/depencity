T = outer_type
U = outer_value


class Base:
    pass


def decorate(value):
    return value


@decorate(T)
def generic_function[T, U](value=T, other=U):
    return value, other


@decorate(T)
class GenericClass[T, U](Base, token=T):
    pass


def create_defaults[T, U, V](first=build(T), second=build(U)):
    return first, second


def create_combined_default[T, U, V](value=build(T, U)):
    return value


class GenericConfigured[T, U, V](Base, first=build(T), second=build(U)):
    pass


def capture_template_default[T](value=t"{T} {external}"):
    return value
