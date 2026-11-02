class A:
    def run(self):
        return first


class B:
    def run(self):
        return second


def sibling_handler_annotations(value: A):
    try:
        work()
    except First:
        value: B
    except Second:
        value.run()
    return value.run()


def sequential_handler_annotations(value: A):
    try:
        work()
    except* First:
        value: B
    except* Second:
        value.run()
    return value.run()


def sibling_case_annotations(subject, value: A):
    match subject:
        case 1:
            value: B
        case 2 if value.run():
            value.run()
    return value.run()


def else_annotations(value: A):
    try:
        work()
    except* Error:
        value: B
    else:
        value.run()
    return value.run()


def completed_body_annotation(value: A):
    try:
        value: B
        work()
    except Error:
        value.run()
    else:
        value.run()
        alias = value
        alias.run()
    return value.run()


def conditional_body_annotation(flag, value: A):
    try:
        if flag:
            value: B
        work()
    except Error:
        pass
    else:
        value.run()
    return value.run()


def main(flag, left: A, right: B):
    value = left
    if flag:
        value = right
    return value.run()


def nested_containers(flag, left: list[list[A]], right: list[list[B]]):
    value = left
    if flag:
        value = right
    return value[0][0].run()


def unknown_rebinding(flag, left: A, right: B, unknown):
    value = left
    if flag:
        value = right
    value = unknown
    return value.run()


def shadowed_alias(value: A):
    class A:
        def run(self):
            return shadowed

    alias = value
    return value.run(), alias.run()


def shadowed_elements(values: list[A], nested: list[list[A]]):
    class A:
        def run(self):
            return shadowed

    item = values[0]
    sequence = nested[0]
    return values[0].run(), item.run(), sequence[0].run()


def local_annotation_origin(value):
    class A:
        def run(self):
            return original

    value: A
    alias = value

    class A:
        def run(self):
            return replacement

    return value.run(), alias.run()


def class_object_origin(factory: type[A]):
    class A:
        def run(self):
            return shadowed

    type = unknown
    alias = factory
    return alias(), alias.run()


def distinct_annotation_origins(flag, left: A, right):
    class A:
        def run(self):
            return local_result

    right: A
    selected = left if flag else right
    return selected.run()


def keep_conditionally_annotated_value(flag):
    if flag:
        from external import UnusedHint
    else:
        from other_external import UnusedHint

    def keep_value(value: UnusedHint):
        return value

    return keep_value


def completed_branch_annotation(flag, value: A):
    if flag:
        value: B
        value.run()
        saved = value
        saved.run()
    else:
        value.run()
    return value.run()


def completed_loop_annotation(items, value: A):
    for item in items:
        value: B
        value.run()
    return value.run()


def interrupted_branch_annotation(flag, value: A):
    if flag:
        try:
            value: B
            value.run()
        except Error:
            value.run()
    return value.run()


def sibling_wrapper_aliases(flag, items, factory):
    Sequence = list
    Class = type
    if flag:
        Sequence = unknown
        Class = unknown
    else:
        items: Sequence[A]
        factory: Class[A]
        return items[0].run(), factory().run()


def replaced_wrapper_aliases(items, factory):
    Sequence = list
    Class = type
    Sequence = unknown
    Class = unknown
    items: Sequence[A]
    factory: Class[A]
    return items[0].run(), factory().run()


def sibling_class_alias(flag, value):
    Class = A
    if flag:
        Class = B
    else:
        value: Class
        return value.run()


def completed_class_alias(flag, value):
    Class = A
    if flag:
        Class = B
        value: Class
        return value.run()
