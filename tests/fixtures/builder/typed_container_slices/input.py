import typing
from typing import Sequence as TypingSequence


class Worker:
    def run(self):
        return 1


def main(values: list[Worker], workers: tuple[Worker, ...]):
    indexed = values[0].run()
    full_slice = values[:].run()
    bounded_slice = values[1:3].run()
    stepped_slice = values[::2].run()
    tuple_slice = workers[1:].run()
    sliced_index = values[:][0].run()
    return (
        indexed,
        full_slice,
        bounded_slice,
        stepped_slice,
        tuple_slice,
        sliced_index,
    )


def saved_index(items: list[Worker]):
    item = items[0]
    alias = item
    return alias.run()


def saved_dynamic_index(items: list[Worker], index: int):
    item = items[index]
    return item.run()


def saved_slice_element(items: list[Worker]):
    sliced = items[:]
    return sliced[0].run()


def saved_slice_receiver(items: list[Worker]):
    sliced = items[:]
    return sliced.run()


def saved_unknown_element(items: other.Sequence[Worker]):
    item = items[0]
    return item.run()


def shadowed_list():
    class list:
        pass

    def use(items: list[Worker]):
        return items[0].run()

    return use


def shadowed_tuple():
    class tuple:
        pass

    def use(items: tuple[Worker, ...]):
        return items[0].run()

    return use


class other:
    class Sequence:
        pass


def unrelated_sequence(items: other.Sequence[Worker]):
    return items[0].run()


def builtin_list(items: list[Worker]):
    return items[0].run()


def builtin_tuple(items: tuple[Worker, ...]):
    return items[0].run()


def annotation_shadow_after(items: list[Worker]):
    list = unknown
    return items[0].run()


def annotation_shadow_nested(items: list[Worker]):
    list = unknown

    def use():
        return items[0].run()

    return use()


def typing_sequence(items: TypingSequence[Worker]):
    return items[0].run()


def qualified_typing_sequence(items: typing.Sequence[Worker]):
    return items[0].run()


class OtherWorker:
    def run(self):
        return 2


def index_rebinds_container(items: list[Worker], replacement: list[OtherWorker]):
    first = items[len(items := replacement)].run()
    return first, items[0].run()


def saved_index_rebinds_container(items: list[Worker], replacement: list[OtherWorker]):
    selected = items[len(items := replacement)]
    return selected.run(), items[0].run()


def nested_index_rebinds_container(
    items: list[list[Worker]], replacement: list[list[OtherWorker]]
):
    first = items[0][len(items := replacement)].run()
    return first, items[0][0].run()


def saved_nested_index_rebinds_container(
    items: list[list[Worker]], replacement: list[list[OtherWorker]]
):
    selected = items[0][len(items := replacement)]
    return selected.run(), items[0][0].run()


class CustomSequence:
    def __getitem__(self, index):
        return self.element

    def run(self):
        return custom_source


def custom_slice(value: CustomSequence):
    sliced = value[:]
    return sliced.run(), value[:].run()


def custom_index(value: CustomSequence):
    selected = value[0]
    return selected.run()


def sliced_factory(factory: type[Worker]):
    sliced = factory[:]
    return sliced()


def mixed_slice(value: Worker | list[Worker]):
    sliced = value[:]
    return sliced.run(), sliced[0].run()


def slice_rebinds_container(items: list[Worker], replacement: list[OtherWorker]):
    sliced = items[:len(items := replacement)]
    return sliced[0].run(), items[0].run()


def quoted_elements(items: list["Worker"], workers: tuple["Worker", ...]):
    return items[0].run(), workers[0].run()


def quoted_compound_elements(items: list["Worker | OtherWorker"]):
    return items[0].run()


def constructed_slice_index(items: list[Worker]):
    selected = items[slice(0, 1)]
    return selected.run()


def named_slice_index(items: list[Worker], selection: slice):
    return items[selection].run()


def replaced_qualified_container():
    import typing as metadata

    metadata.Sequence = CustomSequence
    items: metadata.Sequence[Worker] = source
    return items[0].run()


def captured_qualified_container():
    import typing as metadata

    items: metadata.Sequence[Worker] = source
    metadata.Sequence = CustomSequence
    return items[0].run()


def deleted_qualified_container():
    import typing as metadata

    del metadata.Sequence
    items: metadata.Sequence[Worker] = source
    return items[0].run()
