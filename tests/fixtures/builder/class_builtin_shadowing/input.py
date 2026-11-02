def unbound_free_name(items, replacement):
    class Result:
        value = len(items)

    len = replacement
    return Result


def bound_free_name(items, replacement):
    len = replacement

    class Result:
        value = len(items)

    return Result


def class_local_name(items, replacement):
    len = replacement

    class Result:
        before = len(items)
        len = replacement
        after = len(items)

    return Result


def nested_class(items, replacement):
    class Outer:
        class Inner:
            value = len(items)

    len = replacement
    return Outer


def method_default(items, replacement):
    class Result:
        def action(self, value=len(items)):
            return value

    len = replacement
    return Result


def ordinary_builtin(items):
    class Result:
        value = len(items)

    return Result
