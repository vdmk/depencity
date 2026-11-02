class T:
    def run(self):
        return outer_payload


class Base:
    pass


def main[T](value=wrap(inner(T))):
    return value


def container[T](value=wrap([T])):
    return value


def lambdas[T](captured=lambda: T, shadowed=lambda T: T):
    return captured, shadowed


def comprehensions[T](
    captured=[T for item in items],
    shadowed=[T for T in items],
    deferred=(T for item in items),
):
    return captured, shadowed, deferred


@decorate(T)
def decorated[T](value=inner(T)):
    return value


class Configuration[T](Base, option=wrap(inner(T))):
    pass


class ParameterBase[T](T):
    pass


def read_member(value: ParameterBase):
    return value.run()


def lambda_local_read[T](callback=lambda: (T, (T := replacement))):
    return callback


def lambda_class_alias[T](callback=lambda: ((T := Base), T())):
    return callback


def lambda_builtin_capture[len](callback=lambda values: len(values)):
    return callback


def lambda_builtin_parameter[len](callback=lambda len, values: len(values)):
    return callback


class NestedGenericHeaders:
    class Bounded[T: __bound]:
        pass

    class Defaulted[T=__default]:
        pass

    class Inherited[T](__base):
        pass

    class Configured[T](option=__option):
        pass
