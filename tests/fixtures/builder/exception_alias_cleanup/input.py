def main():
    error = old
    try:
        action()
    except Exception as error:
        consume(error)
    return error


def missing():
    try:
        action()
    except Exception as error:
        consume(error)
    return error


def nested_delete(a, b, old, new):
    x = old
    if a:
        x = new
        if b:
            del x
    return x


def conditional_rebind(flag, replacement):
    try:
        action()
    except Exception as error:
        if flag:
            error = replacement
    return error


def nested_handlers(original):
    error = original
    try:
        action()
    except Exception as error:
        try:
            action()
        except TypeError as error:
            consume(error)
    return error


def nested_handler_read_after_inner(original):
    error = original
    try:
        action()
    except Exception as error:
        try:
            action()
        except TypeError as error:
            consume(error)
        return error


def star_handler(original):
    error = original
    try:
        action()
    except* ValueError as error:
        consume(error)
    return error
