class Plain:
    pass


from builtins import print as display


class Displayed:
    __init__ = display


def builtin_initializer(value):
    return Displayed(value)


class Initialized:
    def __init__(self):
        self.value = 1


class Replacement:
    def run(self):
        return 2


def replace_class(cls):
    return Replacement


def unknown_class(cls):
    return unknown_result


@replace_class
class Decorated:
    def run(self):
        return 3


@unknown_class
class Uncertain:
    def run(self):
        return 4


def decorated_class_call():
    return Decorated().run()


def unknown_decorated_class_call():
    return Uncertain().run()


def main():
    plain_alias = Plain
    initialized_alias = Initialized
    plain = plain_alias()
    initialized = initialized_alias()
    return plain, initialized


def annotated_plain(value: type[Plain]):
    return value()


def annotated_initialized(value: type[Initialized]):
    return value()


def unknown_factory_call(factory):
    return factory()


from external import initialize


class SuppliedInitializer:
    __init__ = initialize


def ordinary_alias_name():
    factory = SuppliedInitializer
    return factory()


def initializer_alias_name():
    __init__ = SuppliedInitializer
    return __init__()


def decorated_alias_chain():
    first = Decorated
    factory = first
    return factory().run()


def hinted_alias_argument(value: type[Plain]):
    factory = value
    return factory(Plain)


class DefaultInitializer:
    def __init__(self, value=default_value):
        self.value = value


class DecoratedInitializer:
    @decorate_initializer
    def __init__(self):
        self.value = 1


class InheritedInitializer(DefaultInitializer):
    pass


def construct_with_declaration_inputs():
    return DefaultInitializer(), DecoratedInitializer(), InheritedInitializer()
