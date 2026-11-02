def helper():
    return 1


del helper


def main():
    return helper()


def versioned():
    return 2


before_read = versioned
before_call = versioned()
del versioned
after_read = versioned
after_call = versioned()


def versioned():
    return 3


rebound_read = versioned
rebound_call = versioned()


def outer():
    def nested_helper():
        return 4

    del nested_helper

    def inner():
        return nested_helper()

    return inner()


def conditional_helper():
    return 5


def conditional(flag):
    global conditional_helper
    if flag:
        del conditional_helper
    return conditional_helper()


conditional_after_delete = conditional_helper


global_value = 7


def delete_global(flag):
    global global_value
    if flag:
        del global_value


def delete_global_from_nested_scope():
    def delete():
        global global_value
        del global_value

    delete()


global_after_delete = global_value


def outer_nonlocal(flag):
    value = 8

    def delete_value():
        nonlocal value
        del value

    if flag:
        delete_value()
    return value


class Receiver:
    def method(self):
        return 6

    def __delitem__(self, index):
        return None


def mutate(value: Receiver, items: Receiver):
    del value.field
    attribute_call = value.method()
    del items[0]
    subscript_call = items.method()
    return attribute_call, subscript_call


def outer_distant(original, flag):
    value = original

    def middle():
        def clear():
            nonlocal value
            if flag:
                del value

        return clear()

    def read():
        return value

    middle()
    return read()


def delete_global_twice(replacement):
    global global_value
    del global_value
    global_value = replacement
    del global_value


def outer_repeated(value, replacement):
    def clear():
        nonlocal value
        del value
        value = replacement
        del value

    def read():
        return value

    clear()
    return read()
