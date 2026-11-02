def main(items, old, stop):
    value = old
    for item in items:
        if item:
            break
    else:
        value = completed
    return value


def nested_break(items, old, stop):
    value = old
    for item in items:
        if stop:
            if item:
                break
    else:
        value = completed
    return value


def terminating_else(items, old):
    value = old
    for item in items:
        if item:
            break
    else:
        return completed
    return value


def while_else(flag, old):
    value = old
    while flag:
        if should_stop:
            if nested_stop:
                break
        flag = False
    else:
        value = exhausted
    return value
