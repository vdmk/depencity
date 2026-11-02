value = original


def remove():
    global value
    before = value
    del value
    after = value
    return before, after


module_after_definition = value


def main(original):
    local = original

    def remove_local():
        nonlocal local
        before = local
        del local
        after = local
        return before, after

    return local


def conditional_remove(flag):
    global value
    before = value
    if flag:
        del value
    after = value
    return before, after


def deferred_class_deletion():
    class Clear:
        global value
        del value


async def deferred_async_deletion():
    global value
    before = value
    del value
    after = value
    return before, after


eager_value = eager_original
before_class = eager_value


class Clear:
    global eager_value
    before = eager_value
    del eager_value
    after = eager_value


after_class = eager_value


def eager_nonlocal(original):
    local = original
    before_class = local

    class Clear:
        nonlocal local
        before = local
        del local
        after = local

    after_class = local
    return before_class, after_class


Example = original


class Example:
    global Example
    del Example


Alias = Example
constructed = Alias()
