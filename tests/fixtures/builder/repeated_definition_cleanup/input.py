def decorate(function):
    return function


def target():
    pass


@decorate
def target():
    pass


def main():
    return target()
