def helper(value=None, *, extra=None):
    return 1


def passed():
    return 2


def extra():
    return 3


def retain_type_default[T](value=T, *, required):
    return value, required
