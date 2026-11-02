def main(value, items):
    total = 0
    if value > 0:
        total = 1
    elif value == 0:
        total = 2
    else:
        total = 3
    if total < 0:
        pass

    for item in items:
        if item is None:
            continue
        total += item
    else:
        total += 1

    index = 0
    while index < len(items):
        index += 1
        if index > 3:
            break
    else:
        total += 2

    try:
        if value == 0:
            raise ValueError("zero")
        total += int(value)
    except ValueError as error:
        total += len(str(error))
    except Exception:
        total -= 1
    else:
        total += 2
    finally:
        total += 0

    with open(path_for("first.txt")) as first, open("second.txt") as second_file:
        content = first.read() + second_file.read()

    match value:
        case 0:
            total += 10
        case int(number) if number > 0:
            total += number
        case {"kind": kind, **rest}:
            total += len(rest) + len(kind)
        case (0, pair_value) | (1, pair_value):
            total += pair_value
        case _:
            total += 20

    assert total >= 0, content
    return total


def parallel(errors):
    handled = errors
    try:
        raise ExceptionGroup("errors", errors)
    except* ValueError as error:
        handled = error
    return handled


def skipped_write(items, skip, old, replacement):
    value = old
    for item in items:
        if skip:
            continue
        value = replacement
    return value


def stopped_write(items, stop, old, replacement):
    value = old
    for item in items:
        if stop:
            break
        value = replacement
    return value


def skipped_delete(items, skip, old, replacement):
    value = old
    for item in items:
        if skip:
            value = replacement
            continue
        del value
    return value
