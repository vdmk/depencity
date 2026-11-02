class First(Second):
    pass


class Second(First):
    pass


def invoke(value: First):
    return value.missing()
