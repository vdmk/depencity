def main(flag, items, produce):
    if flag:
        class Child:
            value = produce()

            class Nested:
                nested_value = produce()

            def method(self):
                return produce()

    for item in items:
        class Iterated:
            value = produce()

    return Child, Iterated
