def value(__return_0__):
    return __return_0__


def generate(__yield_0__):
    yield __yield_0__


def main():
    return value(1)


__return_0__ = 1


def read_module_value():
    return __return_0__


def read_enclosing_value(original):
    __return_0__ = original

    def read():
        return __return_0__

    return read()


def read_from_comprehension(items):
    return [__return_0__ for item in items]


def read_from_generator(items):
    return (__return_0__ for item in items)


def preserve_unbound_local():
    saved = __return_0__
    __return_0__ = 2
    return saved
