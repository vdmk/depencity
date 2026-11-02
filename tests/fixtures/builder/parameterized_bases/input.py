class Base[T]:
    def run(self):
        return 1


class Child(Base[int]):
    pass


class pkg:
    class Base[T]:
        def run(self):
            return 2


class QualifiedChild(pkg.Base[int]):
    pass


def make_base():
    return Base


class DynamicChild(make_base()):
    pass


def main(child: Child, qualified: QualifiedChild, dynamic: DynamicChild):
    return child.run(), qualified.run(), dynamic.run()


class Alternative:
    def run(self):
        return alternative_payload


class RuntimeBase:
    def __class_getitem__(cls, item):
        return Alternative

    def run(self):
        return base_payload


class Subscripted(RuntimeBase[int]):
    pass


def subscripted_base(value: Subscripted):
    return value.run()
