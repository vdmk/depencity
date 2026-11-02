class Base:
    def run(self, value):
        return value

    def dispatch(self):
        return self.choose()

    def choose(self):
        return base_payload


class Child(Base):
    def choose(self):
        return child_payload


def invoke(value):
    return Child.run(value)


def inherited_dispatch():
    return Child().dispatch()
