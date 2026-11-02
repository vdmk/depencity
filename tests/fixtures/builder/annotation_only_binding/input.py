seed = 1
module_value = seed
module_value: int


class Box:
    field: int

    def method(self):
        return 1


class OtherBox:
    def method(self):
        return 2


def main(argument):
    local = argument
    local: int
    inferred = Box()
    inferred: Box
    annotated: Box = Box()
    return (
        module_value,
        local,
        inferred.method(),
        annotated.method(),
    )


def uninitialized_local():
    seed: int
    return seed


def conditional_annotation(value: Box, flag):
    if flag:
        value: OtherBox
    return value.method()


def loop_annotation(value: Box, values):
    for _ in values:
        value: OtherBox
    return value.method()


def unconditional_annotation(value: Box):
    value: OtherBox
    return value.method()


def evaluated_annotation_targets(factory, index):
    factory().value: int
    factory()[(captured := index())]: int


class Fields:
    child: Box


def field_receiver(value: Fields):
    return value.child.method()


def conditional_alias(original: Box, flag):
    value = original
    if flag:
        value: OtherBox
    return value.method()


def make_box() -> Box:
    return external_result


def conditional_factory(flag):
    value = make_box()
    if flag:
        value: OtherBox
    return value.method()


def definite_annotation(original: Box, flag):
    value = original
    if flag:
        value: Box
    value: OtherBox
    return value.method()


def interrupted_factory():
    value = make_box()
    try:
        fail()
        value: OtherBox
        inside = value.method()
    finally:
        result = value.method()
    return result


def suppressed_annotation(value: Box, manager):
    with manager:
        fail()
        value: OtherBox
        inside = value.method()
    return value.method()


def final_annotation(value: Box):
    try:
        fail()
        value: OtherBox
    finally:
        value: Box
    return value.method()


async def suppressed_async_annotation(value: Box, manager):
    async with manager:
        await pause()
        value: OtherBox
    return value.method()


def opposite_annotation(value: Box, flag):
    if flag:
        value: OtherBox
    else:
        return value.method()


def handled_annotation(value: Box):
    try:
        fail()
        value: OtherBox
        inside = value.method()
    except RuntimeError:
        return value.method()


def deleted_receiver(value):
    del value
    value: Box
    return value.method()


def conditionally_deleted_receiver(value, flag):
    if flag:
        del value
    value: Box
    return value.method()
