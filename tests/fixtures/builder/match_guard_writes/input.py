def main(subject, old, replacement):
    value = old
    match subject:
        case 1 if (value := replacement):
            pass
        case int(number) if (value := value + number):
            pass
        case _:
            pass
    return value


captured = None


def capture_global(subject):
    global captured
    match subject:
        case {"value": captured}:
            return captured


def capture_nonlocal(subject, original):
    captured = original

    def capture():
        nonlocal captured
        match subject:
            case {"value": captured}:
                return captured

    return capture()


def capture_local(subject):
    match subject:
        case {"value": captured}:
            return captured


def completed_guard(subject, old, replacement):
    value = old
    match subject:
        case 1 if (value := replacement):
            consume(value)
        case _:
            consume(value)
    return value


def conditional_guard(subject, flag, old, replacement):
    value = old
    match subject:
        case _ if flag or (value := replacement):
            consume(value)
    return value
