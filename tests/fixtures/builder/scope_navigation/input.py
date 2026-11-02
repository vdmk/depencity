def outer(value):
    def inner():
        return value

    return inner()


def enclosing_reassignment(first, second):
    value = first

    def read():
        return value

    before = read()
    value = second
    after = read()
    return before, after
