class Base:
    value = inherited_value
    T = inherited_parameter_name

    def __init__(self):
        self.item = inherited_initializer

    def action(self):
        return inherited_action


class GlobalOnly:
    global action, value

    def action():
        return global_action

    value = global_value
    lexical_read = value


class GlobalChild(Base):
    global action, value, __init__

    def action():
        return global_action

    def __init__(self):
        return global_initializer

    value = global_value
    lexical_read = value


class Generic[T]:
    def read_parameter(self):
        return T


class GenericChild[T](Base):
    def read_parameter(self):
        return T


class AssignedParameter[T]:
    T = class_value


def main():
    return (
        GlobalOnly.action(),
        GlobalOnly.value,
        GlobalChild.action(),
        GlobalChild.value,
        GlobalChild(),
        Generic.T,
        GenericChild.T,
        AssignedParameter.T,
    )


def enclosing():
    action = previous_action
    value = previous_value

    class NonlocalOnly:
        nonlocal action, value

        def action():
            return nonlocal_action

        value = nonlocal_value
        lexical_read = value

    class NonlocalChild(Base):
        nonlocal action, value

        def action():
            return nonlocal_action

        value = nonlocal_value
        lexical_read = value

    return (
        NonlocalOnly.action(),
        NonlocalOnly.value,
        NonlocalChild.action(),
        NonlocalChild.value,
    )
