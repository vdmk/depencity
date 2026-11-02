class A:
    def run(self):
        return 1


def main():
    inline = A().run()
    instance = A()
    saved = instance.run()
    return inline, saved


def unknown_factory(factory):
    return factory().run()


def default_receiver(value=A()):
    return value.run()


def annotated_default_receiver(value: A = A()):
    return value.run()


def passed_receiver(value):
    return value.run()


def pass_instance():
    return passed_receiver(A())
