def f():
    return 1


callable_value = f
f = 2
ordinary_value = f


def main():
    consume(value)
    value = 1
    return value
