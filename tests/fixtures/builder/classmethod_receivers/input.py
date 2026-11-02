class Parent:
    @staticmethod
    def inherited_member():
        return 1

    @classmethod
    def inherited(cls):
        return cls.inherited_member()


class Child(Parent):
    @staticmethod
    def make():
        return 2

    @classmethod
    def build(cls):
        return cls.make()

    def ordinary(cls):
        return cls.make()

    @staticmethod
    def static(cls):
        return cls.make()


def main():
    return Child.build(), Child.inherited(), Child.ordinary(unknown), Child.static(unknown)


class HandlerDecorated:
    def __init__(self):
        initialize()

    decorator = classmethod
    try:
        configure()
    except First:
        decorator = staticmethod
    except Second:
        @decorator
        def make(cls):
            return cls()

    import builtins as decorators
    if selected:
        decorators.classmethod = replacement
    else:
        @decorators.classmethod
        def qualified(cls):
            return cls()
