class A:
    def __init__(self, value):
        self.value = value


class Empty:
    pass


class HasInitializer:
    def __init__(self, value):
        self.value = value


def initialize(self, value):
    self.value = value
