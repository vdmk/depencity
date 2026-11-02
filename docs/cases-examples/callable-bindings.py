def f():
    return 1


first = f


def f():
    return 2


def main():
    return first(), f()
