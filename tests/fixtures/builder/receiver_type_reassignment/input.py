class A:
    def method(self):
        return 1


class B:
    def method(self):
        return 2


def main():
    value = A()
    first = value.method()
    value = B()
    return value.method()


def unknown_reassignment(unknown):
    value = A()
    first = value.method()
    value = unknown
    return value.method()


def conditional_reassignment(flag):
    value = A()
    first = value.method()
    if flag:
        value = B()
    return value.method()


def augmented_reassignment(value: A, other: B):
    value += other
    return value.method()


def augmented_control(value: A):
    return value.method()


global_value: A = A()


def augmented_global(other: B):
    global global_value
    global_value += other
    return global_value.method()


def augmented_nonlocal(other: B):
    value = A()

    def update():
        nonlocal value
        value += other
        return value.method()

    return update()


def select_instances(flag):
    value = A() if flag else B()
    alias = value
    return value.method(), alias.method()


def select_boolean_instances():
    value = A() or B()
    return value.method()


def call_selected_instance(flag):
    return (A() if flag else B()).method()


def ignore_condition_instance():
    value = unknown if A() else unknown
    return value.method()


def ignore_arithmetic_instances():
    value = A() + B()
    return value.method()


def select_annotated(flag, left: A, right: B):
    value = left if flag else right
    alias = value
    return value.method(), alias.method()


def select_boolean_annotations(left: A, right: B):
    value = left or right
    return value.method()


def ignore_condition_annotation(condition: A, unknown):
    value = unknown if condition else unknown
    return value.method()


def ignore_arithmetic_annotations(left: A, right: B):
    value = left + right
    return value.method()


def call_selected_annotation(flag, left: A, right: B):
    return (left if flag else right).method()


def call_boolean_annotation(left: A, right: B):
    return (left or right).method()


def ignore_direct_condition_annotation(condition: A, unknown):
    return (unknown if condition else unknown).method()


def ignore_direct_arithmetic_annotations(left: A, right: B):
    return (left + right).method()


def eager_annotation_read(original, replacement):
    value: A = original

    class Capture:
        result = value.method()

    value: B = replacement
    return Capture.result


def nested_eager_annotation_read(original, replacement):
    value: A = original

    class Outer:
        class Capture:
            result = value.method()

    value: B = replacement
    return Outer.Capture.result


def deferred_annotation_read(original, replacement):
    value: A = original

    def read():
        return value.method()

    value: B = replacement
    return read()


def select_same_class(flag):
    if flag:
        value = A()
    else:
        value = A()
    return value.method()
