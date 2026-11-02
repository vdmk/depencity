class Base:
    def run(self, value):
        return value


class Mixin:
    def run(self, value):
        return value + 1


class Combined(Mixin, Base):
    def run(self, value):
        return super().run(value)


class First:
    method = unknown


class Second:
    def method(self):
        return 2


class Shadowed(First, Second):
    pass


def invoke_shadowed():
    return Shadowed.method()


class ComputedLast(Base, make_base()):
    def run(self, value):
        return super().run(value)


class ComputedFirst(make_base(), Base):
    def run(self, value):
        return super().run(value)


class ExpandedLast(Base, *extra_bases):
    def run(self, value):
        return super().run(value)


class ComputedOnly(make_base()):
    def run(self, value):
        return super().run(value)


def main(value):
    return (
        Combined().run(value),
        ComputedLast().run(value),
        ComputedFirst().run(value),
        ExpandedLast().run(value),
        ComputedOnly().run(value),
    )
