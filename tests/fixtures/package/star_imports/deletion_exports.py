def removed():
    return 1


del removed


def restored():
    return 2


del restored


def restored():
    return 3


def conditional():
    return 4


if condition:
    del conditional


with context as context_value:
    del context_value
    context_value = 5
    with nested_context:
        del context_value
        context_value = 6
    removed_in_context = 7
    del removed_in_context
