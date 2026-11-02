def main(old):
    value = old
    try:
        risky()
    except ValueError:
        value = recovered
    else:
        value = succeeded
        consume(value)
    return value


def exception_before_write(old, fail):
    value = old
    try:
        if fail:
            raise ValueError
        may_raise()
        value = updated
    except ValueError:
        value = recovered
    return value


def guarded_else_assignment(enabled, old, new):
    value = old
    if enabled:
        try:
            risky()
        except ValueError:
            recover()
        else:
            value = new
            consume(value)
    return value


def conditional_else_assignment(flag, old, new):
    value = old
    try:
        risky()
    except ValueError:
        recover()
    else:
        if flag:
            value = new
        consume(value)
    return value


def handler_writes_skipped(old, replacement):
    value = old
    try:
        risky()
    except Error:
        value = replacement
    else:
        consume(value)
    return value


def dispatch_writes_skipped(old, replacement):
    value = old
    try:
        risky()
    except (value := replacement):
        pass
    else:
        consume(value)
    return value


def completed_body_assignment(old, replacement):
    value = old
    try:
        value = replacement
        risky()
    except Error:
        pass
    else:
        consume(value)
    return value


def conditional_body_assignment(flag, old, replacement):
    value = old
    try:
        if flag:
            value = replacement
        risky()
    except Error:
        pass
    else:
        consume(value)
    return value


def completed_global_assignment(replacement):
    global shared
    try:
        shared = replacement
        risky()
    except Error:
        pass
    else:
        consume(shared)
    return shared


shared = initial


def completed_nonlocal_assignment(old, replacement):
    value = old

    def update():
        nonlocal value
        try:
            value = replacement
            risky()
        except Error:
            pass
        else:
            consume(value)
        return value

    return update()


def reassigned_else(flag, replacement, later):
    global shared
    try:
        shared = replacement
        risky()
    except Error:
        pass
    else:
        if flag:
            shared = later
        consume(shared)
        shared += delta
    return shared


def deferred_else(old, replacement, later):
    value = old
    try:
        value = replacement
        risky()
    except Error:
        pass
    else:
        def read():
            return value
        lazy = lambda: value
        pending = (value for item in items)
        eager = [value for item in items]
        value = later
        return read(), lazy(), pending, eager
