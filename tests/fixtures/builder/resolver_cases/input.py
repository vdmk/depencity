from outside import imported


def local_flow(value):
    result = value + 1
    return result


def identity(value):
    return value


def f():
    return 1


def shadowed_function(f):
    return f()


def returns_many(flag):
    if flag:
        return 1
    return 2


def caller(flag):
    return returns_many(flag)


def no_return():
    pass


def caller_without_return():
    return no_return()


def imported_caller():
    return imported()


def builtin_call(items):
    return len(items)


def outer(seed):
    value = seed

    def inner():
        return value

    return inner()


def deep_outer(seed):
    value = seed

    def middle():
        def inner():
            return value

        return inner()

    return middle()


def no_self_dependency():
    value = value
    return value


def branch_reassignment(flag):
    value = 0
    if flag:
        value = 1
    else:
        value = 2
    return value


def sequential_reassignment(value):
    value = value + 1
    value = value + 2
    return value


def temporary_container_selection(value):
    return {None: "missing", "failed": "bad"}.get(value)


table = {"missing": "missing", "failed": "bad"}


def persistent_container_selection(value):
    return table.get(value)
