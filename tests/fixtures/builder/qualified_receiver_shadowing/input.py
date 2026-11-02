class C:
    def method(self):
        return 1


def unshadowed():
    return C.method()


def parameter_shadow(C):
    return C.method()


def typed_parameter_shadow(C: C):
    return C.method()


def local_reassignment():
    C = unknown
    return C.method()


def nested_scope_shadow():
    C = unknown

    def inner():
        return C.method()

    return inner()
