def main(flag):
    x = initial
    if flag:
        x = replacement
    else:
        del x
    y = x
    return y


def reversed_arms(flag):
    x = initial
    if flag:
        del x
    else:
        x = replacement
    y = x
    return y


def same_arm(flag):
    x = initial
    if flag:
        x = replacement
        del x
    y = x
    return y


def nested_opposite(outer, inner):
    x = initial
    if outer:
        if inner:
            x = replacement
        else:
            del x
    y = x
    return y


def nested_same(outer, inner):
    x = initial
    if outer:
        if inner:
            x = replacement
        del x
    y = x
    return y


def overwrite(flag):
    x = initial
    if flag:
        x = replacement
    else:
        del x
    x = final
    y = x
    return y


def named_expression(flag):
    x = initial
    if flag:
        (x := replacement)
    else:
        del x
    y = x
    return y


def short_circuit(flag, ready):
    x = initial
    if flag:
        ready and (x := replacement)
        del x
    y = x
    return y


def conditional_expression(flag, inner):
    x = initial
    if flag:
        (x := left) if inner else (x := right)
    else:
        del x
    y = x
    return y
