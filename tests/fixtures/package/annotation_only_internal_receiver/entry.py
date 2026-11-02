from . import worker as workers
from .facade import Worker as FacadeWorker
from .public import Worker as TwoHopWorker
from .worker import Worker as Work


def aliased(value: Work):
    return value.run()


def class_object_aliased(value: type[Work]):
    return value.run()


def qualified(value: workers.Worker):
    return value.run()


def class_object_qualified(value: type[workers.Worker]):
    return value.run()


def quoted_aliased(value: "Work"):
    return value.run()


def quoted_qualified(value: "workers.Worker"):
    return value.run()


def facade_receiver(value: FacadeWorker):
    return value.run()


def class_object_facade_receiver(value: type[FacadeWorker]):
    return value.run()


def two_hop_receiver(value: TwoHopWorker):
    return value.run()


def missing_facade_member(value: FacadeWorker):
    return value.missing()


def missing(value: Work):
    return value.missing()


def class_object_missing(value: type[Work]):
    return value.missing()


def unsupported_class_object_wrapper(value: type[Work | FacadeWorker]):
    return value.run()


def class_object_annotation_update(value):
    before = value.run()
    value: type[Work]
    return before, value.run()


def local_import():
    from .worker import Worker
    from .other import Unused

    def child(value: Worker):
        return value.run()

    return child


def shadowed_local_import():
    from .other import Worker

    def child(value: Worker):
        return value.run()

    return child


def imported_alias_context(value: Work):
    from .other import Worker as Work

    saved = value
    return value.run(), saved.run()


def imported_element_context(values: list[Work], nested: list[list[Work]]):
    from .other import Worker as Work

    saved = values[0]
    sequence = nested[0]
    return values[0].run(), saved.run(), sequence[0].run()


def qualified_alias_context(value: workers.Worker):
    workers = unknown
    saved = value
    return value.run(), saved.run()


def shadowed_type_wrapper():
    type = wrapper

    def child(value: type[Work]):
        return value.run()

    return child


def local_class_hint():
    class Local:
        def run(self):
            return local_source

    def child(value: Local):
        return value.run()

    return child


def conditional_global_annotation(flag):
    global Work
    if flag:
        from .other import Worker as Work

    def child(value: Work):
        return value.run()

    return child


def conditional_nonlocal_annotation(flag):
    from .worker import Worker

    def change():
        nonlocal Worker
        if flag:
            from .other import Worker

        def child(value: Worker):
            return value.run()

        return child

    return change()


def unconditional_global_annotation():
    global Work
    from .other import Worker as Work

    def child(value: Work):
        return value.run()

    return child


def nested_global_annotation(flag):
    def change():
        global Work
        if flag:
            from .other import Worker as Work

        def child(value: Work):
            return value.run()

        return child

    return change()


forward_value: FutureAlias = unknown
forward_result = forward_value.run()
FutureAlias = Work

forward_module_value: later_workers.Worker = unknown
forward_module_result = forward_module_value.run()
from . import worker as later_workers


def quoted_element_import():
    from .worker import Worker as Element

    def child(values: list["Element"]):
        return values[0].run()

    return child


def quoted_class_import():
    from .worker import Worker as Factory

    def child(value: type["Factory"]):
        return value.run()

    return child


def unused_quoted_import():
    from .other import Unused as Metadata

    def child(values: list["Metadata"]):
        return values

    return child


def quoted_imported_class(value: type["Work"]):
    return value.run()


def quoted_imported_element(values: list["Work"]):
    return values[0].run()
