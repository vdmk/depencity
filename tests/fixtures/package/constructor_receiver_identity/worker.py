class C:
    def method(self):
        return 'worker C'


class D:
    def method(self):
        return 'worker D'


class Base:
    def __init__(self):
        pass


class Derived(Base):
    def method(self):
        return 'worker Derived'


def make_value():
    return 1
