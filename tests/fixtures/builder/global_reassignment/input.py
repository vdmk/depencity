global x
x = 0


def main():
    global x
    x = 1
    return x


def read_before_write(new):
    global x
    previous = x
    x = new
    return previous


def conditional_write(flag, new):
    global x
    if flag:
        x = new
    return x


def augmented_write(new):
    global x
    x += new
    return x


def nested_global_write(new):
    def update():
        global x
        x = new
        return x

    return update()


class EagerGlobalWrites:
    global x
    x = 2

    global new_public
    new_public = 3

    local_only = 4


after_class_write = x
after_new_global = new_public
class_local_control = local_only


class PublishMultipleGlobals:
    global first, second
    first = 1
    second = 2


def read_published_globals():
    return first, second


def read_eager_nonlocal_write(original, replacement):
    value = original
    before = value

    class Update:
        nonlocal value
        value = replacement

    return before, value


def read_conditional_nonlocal_write(original, replacement, flag):
    value = original

    class Update:
        nonlocal value
        if flag:
            value = replacement

    return value


def read_distant_nonlocal_write(original, replacement):
    value = original

    def update():
        class Outer:
            class Inner:
                nonlocal value
                value = replacement

        return value

    return update()


def read_forward_nonlocal_write(first, second):
    class Update:
        nonlocal value
        value = first

    saved = value
    value = second
    return saved


def read_nearest_forward_nonlocal_write(original, first, second):
    value = original

    def update():
        class Update:
            nonlocal value
            value = first

        saved = value
        value = second
        return saved

    return update(), value


def read_annotated_forward_nonlocal_write(first):
    class Update:
        nonlocal value
        value = first

    saved = value
    value: object
    return saved


class PublishAction:
    global published_action

    def published_action():
        return 1


published_function_value = published_action
published_function_call = published_action()


def read_published_function():
    return published_action, published_action()


def read_published_nonlocal_function(action):
    class Publish:
        nonlocal action

        def action():
            return 2

    local_value = action
    local_call = action()

    def read():
        return action, action()

    return local_value, local_call, read()


def isolate_class_nonlocal_write(value, replacement, items):
    class Update:
        nonlocal value
        value = replacement
        inside = value
        eager = [value for item in items]

    return value, Update.inside, Update.eager


module_value = 10


class IsolatedGlobalWrite:
    global module_value
    module_value = 20
    inside = module_value


after_isolated_global_write = module_value


global module_marker
module_marker = source
