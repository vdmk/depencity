def first(value=None):
    return value


def second(value=None):
    return value


module_callback = first
module_result = module_callback(module_callback := second)


def callback_parameter(callback):
    return callback(callback := second)


def local_binding():
    callback = first
    return callback(callback := second)


def unbound_local_callee():
    return callback(callback := second)


def positional_walrus(callback):
    return callback(callback := second)


def keyword_walrus(callback):
    return callback(value=(callback := second))


def unbound_keyword_callee():
    return callback(value=(callback := second))


def shadow_outer_callee():
    callback = first

    def inner():
        return callback(callback := second)

    return inner()


def shadow_builtin_callee():
    return len(len := second)


def repeated_callee_name(callback):
    return callback((callback := second), callback)
