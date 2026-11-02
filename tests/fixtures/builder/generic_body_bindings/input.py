T = outer


def main[T]():
    before = T
    T = replacement
    return before


def explicit_global[T]():
    global T
    return T


def unshadowed[T]():
    return T


def parameter[T](T):
    return T


def ordinary():
    before = T
    T = replacement
    return before


def default_and_local[T](value=T):
    before = T
    T = replacement
    return value, before


def default_and_global[T](value=T):
    global T
    return value, T


def nested[T]():
    def read():
        return T
    return read()


def nested_shadowed[T]():
    def read():
        return T
    T = replacement
    return read()

def builtin_named[len](value=len):
    global len
    return value, len


def nested_callable[T]():
    T = lambda: payload
    def read():
        return T()
    return read()


def generator[T]():
    return (T for item in items)


class Local[T]:
    before = T
    T = replacement
    after = T


class Conditional[T]:
    before = T
    if flag:
        T = replacement
    after = T


class Annotated[T]:
    before = T
    T: Metadata


class Unshadowed[T]:
    before = T
