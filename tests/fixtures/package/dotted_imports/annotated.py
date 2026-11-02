import dotted_imports.nested.worker


def make() -> dotted_imports.nested.worker.Worker:
    return external_result


def named_receiver(value: dotted_imports.nested.worker.Worker):
    return value.run()


def returned_receiver():
    return make().run()


from .nested.worker import Worker


def qualified_generic[Worker](value: dotted_imports.nested.worker.Worker):
    return value.run()


def unqualified_generic[Worker](value: Worker):
    return value.run()
