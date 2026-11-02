def synthetic_collision(__op_0__, a, b):
    result = a + b
    return __op_0__


def a_b():
    return 1


def a():
    def b():
        return 2

    return b()


def main():
    return a_b() + a()
