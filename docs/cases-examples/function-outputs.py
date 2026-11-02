def explicit_return(value):
    return value


def yielded_value(value):
    received = yield value
    return received


def implicit_none():
    pass
