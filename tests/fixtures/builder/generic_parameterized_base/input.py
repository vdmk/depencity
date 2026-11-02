T = replacement


class Base[T]:
    pass


class Child[T](Base[T]):
    pass


def annotation_only(value: T):
    return value
