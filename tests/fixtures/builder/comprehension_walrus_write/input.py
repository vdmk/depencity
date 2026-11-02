def transform(value):
    return value


def main(x, items):
    return [(x := transform(item)) for item in items]


def conditional_capture(flag, items, old, new):
    value = old
    if flag:
        [(value := new, consume(value)) for item in items]
    return value
