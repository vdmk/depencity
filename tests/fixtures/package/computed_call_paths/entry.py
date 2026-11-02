def main(environ):
    return environ["werkzeug.debug.preserve_context"](context)


def call_indexed(_cmpop_to_func, op, args):
    return _cmpop_to_func[op](args)


def call_member(environ, value):
    return environ["key.with.dots"].process(value)


def call_operator_result(a, idx, x):
    return (a[idx] * x**2).sum()


def call_conditional_result(flag, first, second):
    return (first if flag else second).process()


def call_literal_result():
    return (2).bit_length()
