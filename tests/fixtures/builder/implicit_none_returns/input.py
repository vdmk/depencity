def no_return():
    pass


def bare_return():
    return


def conditional_return(flag, value):
    if flag:
        return value


def explicit_returns(flag, first, second):
    if flag:
        return first
    else:
        return second


def raises(error):
    raise error


def finally_raises(value, error):
    try:
        return value
    finally:
        raise error


def main(flag, value, error):
    return (
        no_return(),
        bare_return(),
        conditional_return(flag, value),
        explicit_returns(flag, value, error),
        raises(error),
        finally_raises(value, error),
    )
