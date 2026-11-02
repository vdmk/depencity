def helper():
    return 1


before_read = helper
before_delete = helper()
del helper
after_read = helper
after_delete = helper()


def helper():
    return 2


after_rebind_read = helper
after_rebind = helper()


def optional():
    return 3


if flag:
    del optional

after_conditional_delete = optional()


def main():
    return after_delete


# Callable deletion is outside inference: known targets may survive, or later
# uses may remain unresolved. The explicit deletion is still represented.
class Worker:
    def run(self):
        return class_source


del Worker


def deleted_class_hint(value: Worker):
    return value.run()


def interrupted_delete(value):
    try:
        risky()
        del value
        inside = consume(value)
    except Error:
        recovered = consume(value)
    return value


def suppressed_delete(value, manager):
    with manager:
        risky()
        del value
        inside = consume(value)
    return value
