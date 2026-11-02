def main(value, obj, items):
    assigned = value
    del value
    del obj.field
    del items[0]
    return missing


def delete_only(value):
    del value


def delete_unbound():
    del unknown


def delete_references(obj, items, index):
    del obj.field
    del items[index]


del len


class MissingLocal:
    del list


def delete_missing_global():
    global max
    del max


def augment_global(value):
    global min
    min += value
