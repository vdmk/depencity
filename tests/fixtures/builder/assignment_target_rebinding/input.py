def subscript(x, new, obj, pick):
    obj[(x := pick(new))] = x


def annotated_subscript(x, new, obj, pick):
    obj[(x := pick(new))]: int = x


def attribute(obj, replacement):
    (obj := replacement).value = obj


def control(obj, value, pick):
    obj[pick()] = value


def main(values, replacement, obj, pick):
    for obj[pick(values := replacement)] in values:
        pass
    return obj, values


def attribute_loop(values, replacement):
    for (values := replacement).value in values:
        pass
    return values
