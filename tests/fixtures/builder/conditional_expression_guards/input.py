def main(flag, yes, no, first, second, report):
    choice = yes() if flag else no()
    conjunction = flag and first()
    disjunction = flag or second()
    assert flag, report()
    return choice, conjunction, disjunction


def selected_items(items, flag, left, right):
    return [left if flag else right for item in items]


def selected_calls(items, flag):
    return [first(item) if flag else second(item) for item in items]


def selected_generator(items, flag, left, right):
    return (left if flag else right for item in items)
