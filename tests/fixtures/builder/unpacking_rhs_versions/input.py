def main(values, rows):
    value = values
    value = other = value
    values, tail = values
    values, (head, *nested_tail) = values

    items = rows
    for items, value in items:
        pass

    values, chained_tail = pair = transform(values)
    return tail, nested_tail, value, other, chained_tail, pair


values = (1, (2, 3))


class Box:
    values, tail = values


class NestedBox:
    values, (head, *tail) = values


class ChainedBox:
    values = other = values


def enclosing_function(values):
    class Inner:
        values, tail = values

    return Inner.tail


def read_module_before_enclosing_assignment(replacement):
    class Inner:
        values, tail = values

    values = replacement
    return Inner.tail


def unbound_unpacking():
    values, tail = values
    return tail


def unbound_nested_unpacking():
    values, (head, *tail) = values
    return head, tail


def unbound_chained_assignment():
    values = other = values
    return other
