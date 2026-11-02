len = custom_len
del len

abs = custom_abs
if delete_abs:
    del abs

sum = custom_sum
del sum
sum = replacement_sum

pow = custom_pow


def main(items):
    module_fallback = len(items)
    conditional_fallback = abs(items)
    rebound_call = sum(items)
    global_fallback = delete_global(items)
    local_unbound = delete_local(items)
    return (
        module_fallback,
        conditional_fallback,
        rebound_call,
        global_fallback,
        local_unbound,
    )


def delete_global(items):
    global pow
    del pow
    return pow(items)


def delete_local(items):
    list = local_list
    del list
    return list(items)


class Example:
    all = custom_all
    del all
    size = all(items)


def read_deleted_nonlocal_builtin():
    len = replacement

    def read():
        nonlocal len
        del len
        return len(values)

    return read()


def nested_class_builtin_fallback():
    len = enclosing_len

    class Sized:
        len = local_len
        del len
        size = len(items)

    return Sized


def captured_deleted_local():
    len = enclosing_len
    del len

    class Sized:
        size = len(items)

    return Sized


def round(value):
    return custom_round_payload


if drop_round:
    del round


def round_value(value):
    return round(value)


class Element:
    def run(self):
        return element_payload


list = custom_list
del list
SavedList = list

type = custom_type
del type
SavedType = type


def aliased_container(items: SavedList[Element]):
    return items[0].run()


def aliased_class(factory: SavedType[Element]):
    return factory().run()


def deleted_local_alias(items):
    list = local_list
    del list
    LocalList = list
    items: LocalList[Element]
    return items[0].run()


if enabled:
    max = replacement

    class ShadowedBranch:
        max = 0
        del max
        result = max(value)
else:
    class BuiltinBranch:
        max = 0
        del max
        result = max(value)
