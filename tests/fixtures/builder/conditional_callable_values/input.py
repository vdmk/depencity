def helper():
    return 1


def alternative():
    return 2


class First:
    def __init__(self):
        self.value = 1


class Second:
    def __init__(self):
        self.value = 2


def main(flag):
    selected = helper if flag else helper
    known_choice = selected()

    mixed = helper if flag else external
    mixed_choice = mixed()

    boolean_choice = flag and helper
    known_boolean_choice = boolean_choice()

    condition_only = external if helper else external
    unknown_condition_choice = condition_only()

    arithmetic = helper + flag
    unknown_operator_choice = arithmetic()
    return (
        known_choice,
        mixed_choice,
        known_boolean_choice,
        unknown_condition_choice,
        unknown_operator_choice,
    )


def call_expressions(flag):
    return (
        (helper if flag else alternative)(),
        (helper or alternative)(),
        (flag and helper)(),
        (helper if flag else external)(),
        (external if helper else external)(),
        (helper + flag)(),
        (First if flag else Second)(),
    )


def retain_callable():
    def nested():
        return 1

    saved = nested
    return saved


def provide_action():
    return helper


def returned_action():
    saved = provide_action()
    return saved()


def selected_builtin(flag):
    saved = list if flag else tuple
    return saved(), (list if flag else tuple)(), (list or tuple)()


def mixed_builtin_source(flag):
    saved = helper if flag else list
    return saved()


def direct_builtin():
    return list()


def replace_in_if(flag, replacement):
    selected = helper
    if flag:
        selected = replacement
        selected()
    return selected()


def replace_in_while(flag, replacement):
    selected = helper
    while flag:
        selected = replacement
        selected()
    return selected()


def replace_in_for(items, replacement):
    selected = helper
    for item in items:
        selected = replacement
        selected()
    return selected()


def replace_class_in_if(flag):
    factory = First
    if flag:
        factory = Second
        factory()
    return factory()


def after_return_guard(stop, replacement):
    selected = helper
    if stop:
        return None
    selected = replacement
    return selected()


def after_raise_guard(stop, replacement):
    selected = helper
    if stop:
        raise ValueError
    selected = replacement
    return selected()


def conditional_after_guard(stop, change, replacement):
    selected = helper
    if stop:
        return None
    if change:
        selected = replacement
    return selected()


def read_in_else(flag):
    selected = helper
    if flag:
        selected = alternative
    else:
        selected()
    return selected()


def read_in_elif(flag):
    selected = helper
    if flag:
        selected = alternative
    elif selected():
        pass
    return selected()


def class_in_else(flag):
    factory = First
    if flag:
        factory = Second
    else:
        factory()
    return factory()


def selected_expression(flag):
    selected = helper
    result = (selected := alternative) if flag else selected()
    return result, selected


def eager_class_in_else(flag):
    selected = helper
    if flag:
        selected = alternative
    else:
        class Capture:
            value = selected()
        return Capture


def completed_boolean(flag):
    selected = helper
    result = flag and ((selected := alternative), selected())
    return result, selected


def completed_boolean_chain(flag):
    selected = helper
    result = flag and (selected := alternative) and selected()
    return result, selected


def completed_conditional_operand(flag):
    selected = helper
    result = ((selected := alternative), selected()) if flag else None
    return result, selected


module_selected = helper
if halt:
    raise RuntimeError
module_selected = module_replacement
module_result = module_selected()
