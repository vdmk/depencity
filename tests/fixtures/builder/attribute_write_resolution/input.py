class Worker:
    VALUE = original


def main(value: Worker, replacement, increment):
    value.VALUE = 1
    value.VALUE = replacement
    value.VALUE += increment
    del value.VALUE


class Container:
    class Worker:
        @staticmethod
        def run():
            return 1


def replace_intermediate(replacement):
    Container.Worker = replacement
    return Container.Worker.run()


def delete_intermediate():
    del Container.Worker
    return Container.Worker.run()


def call_before_intermediate_write(replacement):
    before = Container.Worker.run()
    Container.Worker = replacement
    return before, Container.Worker.run()


def write_sibling(replacement):
    Container.WorkerExtra = replacement
    return Container.Worker.run()


def write_descendant(replacement):
    Container.Worker.run.extra = replacement
    return Container.Worker.run()


class Shared:
    @staticmethod
    def run():
        return declared_payload


def replacement_method():
    return replacement_payload


Shared.run = replacement_method


def read_shared():
    return Shared.run()


def replace_shared(replacement):
    Shared.run = replacement
    return Shared.run()


def replace_nested_method(replacement):
    Container.Worker.run = replacement
    return Container.Worker.run()


def delete_nested_method():
    del Container.Worker.run
    return Container.Worker.run()


def nested_call_before_write(replacement):
    before = Container.Worker.run()
    Container.Worker.run = replacement
    return before, Container.Worker.run()


class OtherContainer:
    class Worker:
        @staticmethod
        def run():
            return other_payload


def nested_write_rebinds_receiver():
    container = Container
    container.Worker.run = (container := OtherContainer)
    return container.Worker.run()


def direct_write_rebinds_receiver():
    worker = Container.Worker
    worker.run = (worker := OtherContainer.Worker)
    return worker.run()


def indexed_member_write(items: list[Shared], replacement):
    items[0].run = replacement
    return items[0].run()


def make_shared() -> Shared:
    return external_source


def computed_member_write(replacement):
    make_shared().run = replacement
    return make_shared().run()


def instances_after_class_write(replacement):
    existing = Shared()
    Shared.run = replacement
    created = Shared()
    return Shared.run(), existing.run(), created.run()


def alias_after_class_write(replacement):
    alias = Shared
    Shared.run = replacement
    return alias.run()


def opposite_branch(flag, replacement):
    if flag:
        Container.Worker.run = replacement
    else:
        return Container.Worker.run()
    return Container.Worker.run()


def sibling_handlers(replacement):
    try:
        configure()
    except First:
        Container.Worker.run = replacement
    except Second:
        return Container.Worker.run()


def sequential_handlers(replacement):
    try:
        configure()
    except* First:
        Container.Worker.run = replacement
    except* Second:
        Container.Worker.run()


def sibling_cases(subject, replacement):
    match subject:
        case 1:
            Container.Worker.run = replacement
        case 2:
            return Container.Worker.run()
