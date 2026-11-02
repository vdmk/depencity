class Known:
    def run(self):
        return known_payload


Alias = Known
Chained = Alias
Extracted, other = Known


class Namespace:
    Alias = Known
    Extracted, other = Known


class Wrapper:
    def __init__(self, function):
        self.function = function

    def run(self):
        return wrapper_payload


@Wrapper
def Decorated():
    return function_payload


def choose(function):
    return Known


@choose
def Resolved():
    pass


def main(value: Extracted):
    return value.run()


def qualified(value: Namespace.Extracted):
    return value.run()


def decorated(value: Decorated):
    return value.run()


def ordinary_alias(value: Alias):
    return value.run()


def chained_alias(value: Chained):
    return value.run()


def qualified_alias(value: Namespace.Alias):
    return value.run()


def resolved_decorator(value: Resolved):
    return value.run()


def constructor(value: type[Extracted]):
    instance = value()
    return instance.run()


def container(values: list[Extracted]):
    return values[0].run()


class ChangedNamespace:
    Item = Known


ChangedNamespace.Item = replacement


def overwritten_member(value: ChangedNamespace.Item):
    return value.run()


def overwritten_local_member(value, replacement):
    class Local:
        Item = Known

    Local.Item = replacement
    value: Local.Item
    return value.run()


def retained_local_annotation(value, replacement):
    class Local:
        Item = Known

    value: Local.Item
    Local.Item = replacement
    return value.run()


def deleted_local_member(value):
    class Local:
        Item = Known

    del Local.Item
    value: Local.Item
    return value.run()


def conditionally_written_member(flag, value, replacement):
    class Local:
        Item = Known

    if flag:
        Local.Item = replacement
    else:
        value: Local.Item
        return value.run()
