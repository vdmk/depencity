def helper(first=None, *, second=None, third=None):
    return 1


def first():
    return 2


def second():
    return 3


def third():
    return 4


def main():
    positional = helper(first)
    keyword = helper(second=second)
    multiple = helper(first, second=second, third=third)
    return positional, keyword, multiple


def ignores_argument(value):
    return 1


same_name_as_callee = ignores_argument(ignores_argument)


def pass_self_by_keyword():
    return ignores_argument(value=ignores_argument)


class Consumer:
    pass


same_class_as_callee = Consumer(Consumer)


def abort(value):
    raise RuntimeError("stop")


abort_alias = abort
abort_alias(abort)
abort_alias(value=abort)
abort_alias(Consumer)

consumer_alias = Consumer
consumer_alias(Consumer)
