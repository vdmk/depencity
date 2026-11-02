from .worker import helper, other


def main():
    global other
    return helper(other, extra=(other := 3))
