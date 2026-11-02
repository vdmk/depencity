global_alias = len
global_result = global_alias(values)


def main(values):
    f = len
    return f(values)


def direct(values):
    return len(values)


def chain(values):
    first = len
    second = first
    last = second
    return last(values)


def callback(f, values):
    return f(values)


def constructed(values):
    f = wrap(len)
    return f(values)


def container(values):
    f = [len]
    return f(values)


def unpacked(values):
    f, = (len,)
    return f(values)


def captured(other):
    f = len
    return f(f := other)


def rebound(other):
    f = other
    return f((f := len), f)


def shadowed(len, values):
    f = len
    return f(values)


def overwritten(other, values):
    f = len
    f = other
    return f(values)


def unknown_member(values):
    f = len
    return f.missing(values)


def unpacked_builtin():
    alias, other = len
    return alias()


def iterated_builtin():
    for alias in len:
        return alias()


def accepts_builtin(value=len):
    return payload


def call_with_default():
    alias = accepts_builtin
    return accepts_builtin(), alias()


def produces_builtin():
    return len


def call_producer():
    alias = produces_builtin
    return produces_builtin(), alias()


def module_metadata():
    return __name__, __doc__, __package__, __loader__, __spec__, __file__


def local_metadata(__name__):
    __doc__ = source
    return __name__, __doc__


def explicit_builtin_metadata():
    from builtins import __name__ as builtin_name

    return builtin_name


class BuiltinMembers:
    length = len


def builtin_member(values):
    return BuiltinMembers.length(values)


def saved_builtin_member(values):
    saved = BuiltinMembers.length
    return saved(values)
