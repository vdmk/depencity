class Base:
    def __init__(self, value):
        self.value = value


class Middle(Base):
    pass


class Deep(Middle):
    pass


class Override(Base):
    def __init__(self, value):
        self.value = value


class NoInitBase:
    pass


class NoInit(NoInitBase):
    pass


class Replaced(Base):
    __init__ = unknown


def main(value):
    return (
        Base(value),
        Deep(value),
        Override(value),
        NoInit(value),
        Replaced(value),
    )


if enabled:
    class GuardedOverride(Base):
        def __init__(self, value):
            self.value = value

    class GuardedInherited(Base):
        pass


def guarded_constructors(value):
    return GuardedOverride(value), GuardedInherited(value)


def replaced_initializer(value, replacement):
    Base.__init__ = replacement
    return Base(value), Base.__init__(value)


def deleted_initializer(value):
    del Base.__init__
    return Base(value), Base.__init__(value)
