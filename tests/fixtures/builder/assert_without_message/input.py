def main(value):
    assert value
    return value


def guarded_result(flag, value, consume):
    assert flag
    result = consume(value)
    return result


def caught_assertion(flag, value):
    try:
        assert flag
    except AssertionError:
        pass
    return value


def suppressed_assertion(manager, flag, value):
    with manager:
        assert flag
    return value
