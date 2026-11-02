def helper(value, extra):
    return value


def main():
    def other():
        return 2

    return helper(other, (other := 3))


def local_callee():
    def f(value):
        return value

    def second():
        return 2

    return f(f := second)
