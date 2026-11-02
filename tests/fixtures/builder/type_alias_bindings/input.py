type Alias = int

type GenericAlias[T] = list[T]


def return_alias():
    return Alias


def annotation_only(value: Alias):
    return value


def generic_function[T](value: T):
    return T


class GenericClass[T]:
    def parameter(self):
        return T


class ShadowedTypeParameter[T]:
    T = replacement

    def parameter(self):
        return T


def outer_function[T]():
    T = replacement

    def inner():
        return T

    return inner


class MethodWithNestedFunction[T]:
    def method(self):
        T = replacement

        def inner():
            return T

        return inner


class Worker:
    def run(self):
        return payload


type WorkerAlias = Worker
PlainAlias = Worker


def lazy_alias(value: WorkerAlias):
    return value.run()


def ordinary_alias(value: PlainAlias):
    return value.run()
