def helper(value=None):
    return 1


def other(value=None):
    return 2


def captured_callee():
    callback = helper
    return callback(lambda value=(callback := other): value)


def tuple_values(value, replacement):
    return value, (lambda item=(value := replacement): item)


def conditional_default(flag, value, replacement):
    result = flag and (lambda item=(value := replacement): item)
    return result, value


def deferred_body(flag, value, replacement):
    result = flag and (lambda: (value := replacement))
    return result, value


def discard_lambda(value):
    lambda: value
