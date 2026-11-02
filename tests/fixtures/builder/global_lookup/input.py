global missing_value, missing_action, len, conditional_value, deleted_value

x = "module"

before_conditional = conditional_value
if flag:
    conditional_value = source
after_conditional = conditional_value

deleted_value = source
del deleted_value
after_delete = deleted_value


def outer():
    x = "outer"

    def inner():
        global x
        return x

    return inner()


def main():
    return outer()


def read_declared_globals(items):
    return (
        missing_value,
        missing_action(),
        len(items),
        conditional_value,
        deleted_value,
    )


def first():
    return 1


def second():
    return 2


action = first


class GlobalCapture:
    global action
    result = action()

    class NestedCapture:
        global action
        result = action()


action = second


def eager_nonlocal_read():
    action = first

    class Capture:
        nonlocal action
        result = action()

    action = second
    return Capture.result


def nested_eager_nonlocal_read():
    action = first

    class Outer:
        class Capture:
            nonlocal action
            result = action()

    action = second
    return Outer.Capture.result


def global_skips_function_local():
    action = first

    class Capture:
        global action
        result = action()

    return Capture.result


def deferred_nonlocal_read():
    action = first

    def read():
        nonlocal action
        return action()

    action = second
    return read()


class MatchCapture:
    global match_value

    match subject:
        case match_value:
            pass


captured_match = match_value
