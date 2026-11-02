class A:
    def method(self):
        return 1


class B:
    def method(self):
        return 2


def create_member():
    return A()


class Holder:
    value = create_member()
    value: A
