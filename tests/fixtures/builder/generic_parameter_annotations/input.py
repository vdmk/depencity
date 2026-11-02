class T:
    def run(self):
        return outer_payload

    class Inner:
        def run(self):
            return nested_payload


class Known:
    def run(self):
        return known_payload


def main[T](value: T):
    return value.run()


def ordinary(value: T):
    return value.run()


def qualified[T](value: T.Inner):
    return value.run()


def quoted[T](value: "T"):
    return value.run()


def container[T](values: list[T]):
    return values[0].run()


def factory[T](value: type[T]):
    obj = value()
    return obj.run()


def shadowed_type[type](value: type[Known]):
    obj = value()
    return obj.run()


def shadowed_list[list](values: list[Known]):
    return values[0].run()


def mixed[T](value: T | Known):
    return value.run()


def body_local[T](value: Known):
    class Known:
        def run(self):
            return wrong_local_payload

    return value.run()


def bounded[T: Known](value: T):
    return value.run()


def forward[T](value: "Later"):
    return value.run()


class Later:
    def run(self):
        return forward_payload


class Methods:
    def generic[T](self, value: T):
        return value.run()

    def ordinary(self, value: T):
        return value.run()


class GenericClass[T]:
    def method(self, value: T):
        return value.run()


def nested[T]():
    def read(value: T) -> T:
        return value
    return read
