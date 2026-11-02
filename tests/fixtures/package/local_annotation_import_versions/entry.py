def control(value):
    from .worker import Worker
    value: Worker
    return value.run()


def main(value):
    from .worker import Worker
    value: Worker
    Worker = other
    return value.run()


def aliased(value):
    from .worker import Worker as Work
    value: Work
    saved = value
    Work = other
    return saved.run()


def elements(values):
    from .worker import Worker
    values: list[Worker]
    Worker = other
    return values[0].run()


def import_rebinding(value):
    from .worker import Worker
    value: Worker
    from .other import Worker
    return value.run(), Worker().run()


def unused_hint(value):
    from .worker import Worker
    value: Worker
    Worker = other
    return value


def sibling_import(flag, value):
    from .worker import Worker
    if flag:
        from .other import Worker
    else:
        value: Worker
        return value.run()


def completed_import(flag, value):
    from .worker import Worker
    if flag:
        from .other import Worker
        value: Worker
        return value.run()


def overwritten_qualified_hint(value, replacement):
    from . import worker
    worker.Worker = replacement
    value: worker.Worker
    return value.run()


def retained_qualified_hint(value, replacement):
    from . import worker
    value: worker.Worker
    worker.Worker = replacement
    return value.run()
