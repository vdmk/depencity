class Original:
    value = source_value

    def __init__(self, value):
        self.value = value

    def method(self):
        return self.value


Exported = Original
Chained = Exported
Instance = Original(source_value)


class Container:
    Nested = Original


Rebound = Original
Rebound = unknown
Extracted, other = Original

Nested = Original


def select_same_constructor(flag):
    from . import worker as module

    if flag:
        receiver = module
    else:
        receiver = Container
    return receiver.Nested(Original)
