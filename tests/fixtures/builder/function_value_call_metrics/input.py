def helper():
    return 1


def unknown_call():
    return external(helper)


def returned_value():
    return helper


def direct_call():
    return helper()


def builtin_alias_call():
    callback = len
    return callback([])


def returned_callable_is_unknown():
    callback = make(len)
    return callback([])
