from . import worker


def invoke(value: worker.Worker):
    return value.run()


import initialized_module_annotation.nested.models


def make() -> initialized_module_annotation.nested.models.Worker:
    return external_result


def factory_results():
    saved = make()
    return saved.run(), make().run()


def qualified_generic[Worker](value: initialized_module_annotation.nested.models.Worker):
    return value.run()
