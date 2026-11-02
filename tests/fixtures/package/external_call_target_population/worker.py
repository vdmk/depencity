def helper(flag):
    return 1


def multiple(flag):
    if flag:
        return 1
    return 2


def generated(flag):
    if flag:
        yield 1
    yield 2
