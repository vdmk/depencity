class Publisher:
    global public_value
    public_value = 1
    class_local_value = 2


def _transform(value):
    return value


class AnnotationPublisher:
    global attribute_global
    (attribute_global := _transform).field: int
    class_annotation_only: int


class SubscriptAnnotationPublisher:
    global subscript_global
    _holder = {}
    _holder[(subscript_global := _transform)]: int


class ComprehensionLocals:
    global list_item, set_item, dict_item, generator_item, nested_item
    values = [list_item for list_item in source]
    unique = {set_item for set_item in source}
    mapping = {dict_item: dict_item for dict_item in source}
    stream = (generator_item for generator_item in source)
    nested = [nested_item for group in groups for nested_item in group]
