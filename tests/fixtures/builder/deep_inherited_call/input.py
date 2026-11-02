class Grand:
    def run(self, value):
        return value


class Parent(Grand):
    pass


class Child(Parent):
    pass


def invoke(value: Child):
    return value.run(value)
