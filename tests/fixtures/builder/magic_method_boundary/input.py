class Value:
    def __bool__(self):
        return bool_payload

    def __add__(self, other):
        return add_payload

    def __getitem__(self, index):
        return item_payload

    def __iter__(self):
        return iterator_payload


def main(value: Value, other, index):
    return not value, value + other, value[index]


def implicit_truth(value: Value):
    try:
        if value:
            pass
    except Exception:
        recover()


def implicit_iteration(value: Value):
    try:
        for item in value:
            pass
    except Exception:
        recover()


def explicit_calls(value: Value, other, index):
    return value.__bool__(), value.__add__(other), value.__getitem__(index), value.__iter__()
