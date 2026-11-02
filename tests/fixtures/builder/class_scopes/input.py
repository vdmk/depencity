def module_fn(value):
    return value


class Base:
    def inherited(self, value):
        return value


class Box:
    def __init__(self, value):
        self.value = value

    def method(self, value):
        return value


class Child(Base):
    def inherited(self, value):
        return super().inherited(value)


class Mixin:
    def mix(self, value):
        return value


class Combined(Mixin, Base):
    pass


class ReceiverNames:
    def read_self(self):
        return self.value

    def read_renamed(this):
        return this.value

    def write_renamed(this, value):
        this.value = value
        del this.old_value
        return this.child.value

    @classmethod
    def read_class(receiver):
        receiver.value = receiver.default
        return receiver.value

    @staticmethod
    def read_static(self):
        return self.value

    def read_closure(this):
        def read():
            return this.value

        def shadow(this):
            return this.value

        return read, shadow

    def read_rebound(this, replacement):
        before = this.value
        this = replacement
        return before, this.value


def read_self_parameter(self):
    return self.value


def main(value):
    box: Box = Box()
    return box.method(value)


def annotated(box: Box, value):
    return box.method(value)


def inherited(child: Child, value):
    return child.inherited(value)


def mixin(value: Combined):
    return value.mix(value)


def dynamic(instance, value):
    return instance.method(value)
