from .worker import Worker


def main(value):
    worker: Worker = Worker()
    return worker.run(value)


@unknown_decorator
class Decorated:
    def create(self):
        alias = __class__
        return alias()

    def create_child(self):
        Base = __class__

        class Child(Base):
            pass

        return Child()

    def annotate_before_global_alias(self, value):
        global Alias
        value: Alias
        Alias = __class__
        return value.run()
