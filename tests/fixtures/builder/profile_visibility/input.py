def outer(value):
    def inner():
        nonlocal value
        value = value
        return print(value)

    return inner


def producer(value):
    return value


def consumer(value):
    return producer(value) + missing + missing
