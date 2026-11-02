def main(call_x, container_x, operator_x, new):
    call_result = external(call_x, (call_x := new))
    container_result = (container_x, (container_x := new))
    operator_result = operator_x + (operator_x := new)
    return call_result, container_result, operator_result


def unbound_operator(replacement):
    return value + (value := replacement)


def unbound_container(replacement):
    return value, (value := replacement)


def unbound_argument(replacement):
    return external(value, (value := replacement))


def shadow_builtin(replacement):
    return len, (len := replacement)


def read_after_binding(replacement):
    return (value := replacement), value


def deferred_lambda(replacement):
    return (lambda: value), (value := replacement)


def eager_lambda_default(replacement):
    return (lambda prior=value: prior), (value := replacement)


def conditional_read(flag, old, new):
    value = old
    if flag:
        value = new
    return value, (value := new)
