def helper():
    return 1


def alias_chain():
    first = helper
    second = first
    return second()


def conditional_alias(flag):
    if flag:
        callable_value = helper
    else:
        callable_value = external
    return callable_value()


def rebinding_alias():
    callable_value = helper
    known_result = callable_value()
    callable_value = external
    unknown_result = callable_value()
    return known_result, unknown_result


def supplied_as_argument():
    return takes_function(helper)


def call_result_is_not_its_argument():
    possible_callable = takes_function(helper)
    return possible_callable()


def read_value():
    return 1


read_value = external
reassigned_result = read_value()


def main():
    return reassigned_result


def defaulted(value=seed):
    return payload


def defaulted_alias():
    selected = defaulted
    return selected()


def extracted_callable():
    selected, other = defaulted
    return selected()


def fail():
    raise failure


def fail_with_default(value=seed):
    raise value


def nonreturning_aliases():
    first = fail
    second = first
    defaulted = fail_with_default
    first()
    second()
    defaulted()


def direct_failure():
    fail()
