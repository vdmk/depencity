def main(old):
    value = old
    try:
        risky()
    except:
        value = recovered
    return value


def handler_without_write(old):
    value = old
    try:
        risky()
    except:
        recover()
    return value


def with_else_and_finally(old):
    value = old
    try:
        risky()
    except:
        value = recovered
    else:
        value = succeeded
    finally:
        value = cleanup(value)
    return value
