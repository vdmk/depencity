class Replaced:
    def run(self):
        return earlier_payload


class Replaced:
    eager = Replaced().run()

    def run(self):
        return current_payload

    def read(self, value: Replaced):
        return value.run()

    def quoted(self, value: "Replaced"):
        return value.run()

    def generic[Replaced](self, value: Replaced):
        return value.run()

    def default(self, value=Replaced()):
        return value


class Forward:
    def read(self, value: Later):
        return value.run()


class Later:
    def run(self):
        return later_payload


class Outer:
    class Nested:
        def run(self):
            return nested_payload

        def read(self, value: "Outer.Nested"):
            return value.run()


class Namespace:
    class Replaced:
        def run(self):
            return class_local_payload

    def read(self, value: Replaced):
        return value.run()


def enclosing():
    class Local:
        def run(self):
            return enclosing_payload

        def read(self, value: "Local"):
            return value.run()

    return Local


def main(value: Replaced):
    return value.run()


__class__ = Later


class SelfTyped:
    def run(self):
        return self_typed_payload

    def read(self, value: __class__):
        return value.run()

    def make(self) -> __class__:
        return source


class ShadowedCell:
    __class__ = SelfTyped

    def read(self, value: __class__):
        return value.run()


class GlobalCell:
    global __class__

    def read(self, value: __class__):
        return value.run()


def self_typed_result(value: SelfTyped):
    result = value.make()
    return result.run()


class GenericCell[__class__]:
    def run(self):
        return generic_cell_payload

    def read(self, value: __class__):
        return value.run()

    def opaque[__class__](self, value: __class__):
        return value.run()
