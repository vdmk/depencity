class Outer:
    class Inner:
        pass


def main(value):
    value: Outer
    return value.Inner.missing()
