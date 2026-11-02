class C:
    def method(self):
        return 1


class D:
    def method(self):
        return 2


direct_before = C.method()
C = unknown
direct_after = C.method()


if flag:
    D = unknown


def parameter_shadow(C):
    return C.method()


def typed_parameter_shadow(C: D):
    return C.method()


def enclosing_reassignment():
    C = unknown

    def inner():
        return C.method()

    return inner()


def conditional_receiver():
    return D.method()


def main():
    return (
        C.method(),
        D.method(),
        parameter_shadow(unknown),
        typed_parameter_shadow(unknown),
        enclosing_reassignment(),
        conditional_receiver(),
    )
