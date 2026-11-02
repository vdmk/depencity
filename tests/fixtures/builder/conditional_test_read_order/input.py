flag = initial
result = left if flag else (flag := replacement)


def main(left, replacement):
    flag = initial
    return left if flag else (flag := replacement)


def unbound(left, replacement):
    return left if flag else (flag := replacement)


def explicit_global(left, replacement):
    global flag
    return left if flag else (flag := replacement)


def enclosing(left, replacement):
    flag = initial

    def explicit_nonlocal():
        nonlocal flag
        return left if flag else (flag := replacement)

    return explicit_nonlocal()


def nested(outer, left, replacement):
    flag = initial
    return (left if flag else (flag := replacement)) if outer else fallback


def true_branch(left, replacement):
    flag = initial
    return (flag := replacement) if flag else left


def unchanged(flag, left, right):
    return left if flag else right
