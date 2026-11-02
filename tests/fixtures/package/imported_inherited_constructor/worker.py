from .base import HasInitializer, initialize


class Base:
    def __init__(self, value):
        self.value = value


class Middle(Base):
    pass


class Imported(Middle):
    pass


class Conditional:
    if enabled:
        def method(self):
            return 1
    else:
        def method(self):
            return 2


class ComputedBase(make_base()):
    pass


class GlobalInitializer(Base):
    global __init__

    def __init__(self, value):
        return wrong_initializer


class AliasedInitializer:
    __init__ = initialize


class GlobalOnly:
    global __init__

    def __init__(self, value):
        return unrelated_initializer


class LaterInitializer(GlobalOnly, HasInitializer):
    pass
