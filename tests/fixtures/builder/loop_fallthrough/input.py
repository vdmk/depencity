def main(items, seed):
    x = seed
    for item in items:
        x = 1
    return x


def for_with_break(items, seed):
    value = seed
    for item in items:
        value = item
        if item:
            break
    return value


def while_with_break(flag, seed):
    value = seed
    while flag:
        value = next_value
        if should_stop:
            break
        flag = False
    return value


def guarded_continue(items, seed):
    value = seed
    for item in items:
        if item is None:
            continue
        value = item
    return value


def for_carried_binding(items, initial, replacement):
    value = initial
    for item in items:
        consume(value)
        value = replacement
    return value


def while_carried_binding(initial, replacement):
    value = initial
    while ready(value):
        consume(value)
        value = replacement
    return value
