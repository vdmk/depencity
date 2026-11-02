x = original


def main(new, flag):
    global x
    call_result = external(x, (x := new), x)
    call_after = external(x)
    container_result = (x, (x := new), x)
    container_after = (x, x)
    operator_result = x + (x := new)
    operator_after = x + 1
    if flag:
        x = conditional_value
    conditional_result = external(x)

    def nonlocal_cases(new_value, conditional_flag):
        value = original

        def call_case():
            nonlocal value
            result = external(value, (value := new_value), value)
            return result, external(value)

        def container_case():
            nonlocal value
            result = (value, (value := new_value), value)
            return result, (value, value)

        def operator_case():
            nonlocal value
            result = value + (value := new_value)
            return result, value + 1

        def conditional_case():
            nonlocal value
            if conditional_flag:
                value = conditional_value
            return external(value)

        return call_case, container_case, operator_case, conditional_case

    return (
        call_result,
        call_after,
        container_result,
        container_after,
        operator_result,
        operator_after,
        conditional_result,
        nonlocal_cases,
    )
