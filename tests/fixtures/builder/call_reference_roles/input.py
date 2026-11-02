from unavailable import action as imported_action


def main(obj):
    return obj.method(obj.method)


def shared_binding(action):
    return action(action)


def shared_import():
    return imported_action(imported_action)


def source():
    return payload


def zero_input_callee():
    (0)(source)
    (0)(source, source)


def unknown_callee():
    unknown(source)


def shared_source():
    source(source, source)
    alias = source
    alias(alias)


def computed_callee(flag, left, right):
    return (left if flag else right)(left, right)


class Holder:
    value = member_payload


def attribute_argument():
    return (0)(Holder.value)


def known_attribute_argument():
    return source(Holder.value)
