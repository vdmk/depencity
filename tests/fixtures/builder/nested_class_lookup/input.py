x = 1


class A:
    x = 2

    class B:
        y = x
        missing = outer_only


class Holder:
    class Nested:
        qualified = A.x


def factory():
    x = 3

    class Outer:
        x = 4

        class Inner:
            y = x

        class Own:
            x = 5
            y = x

    return Outer


class BuiltinOuter:
    len = 99

    class Inner:
        count = len(values)


def main():
    return factory()
