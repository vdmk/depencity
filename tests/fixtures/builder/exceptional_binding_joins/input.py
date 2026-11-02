def main():
    x = initial
    try:
        fail()
        x = replacement
    finally:
        y = x
    return y


def with_body(manager):
    x = initial
    with manager:
        fail()
        x = replacement
        inside = x
    y = x
    return inside, y


async def async_body(manager):
    x = initial
    async with manager:
        await fail()
        x = replacement
    y = x
    return y


def named_expression(manager):
    x = initial
    with manager:
        fail()
        (x := replacement)
    y = x
    return y


def nested_contexts(first, second):
    x = initial
    with first:
        with second:
            fail()
            x = inner
        after_inner = x
        x = outer
        inside = x
    y = x
    return after_inner, inside, y


def overwrite(manager):
    x = initial
    with manager:
        fail()
        x = replacement
    x = final
    y = x
    return y


def finally_overwrite():
    x = initial
    try:
        fail()
        x = replacement
    finally:
        x = final
    y = x
    return y


def caught_body():
    x = initial
    try:
        fail()
        x = replacement
    except Exception:
        pass
    y = x
    return y


def completed_assignment(old, new):
    x = old
    try:
        x = new
        consume(x)
    except Error:
        recover(x)
    return x


def entry_target(manager):
    x = initial
    with manager as x:
        pass
    y = x
    return y


def multiple_entries(first, second):
    x = initial
    with first, second as x:
        pass
    y = x
    return y


def unpacked_entry(manager):
    x = initial
    with manager as (other, x):
        pass
    y = x
    return y


def deletion(manager):
    x = initial
    with manager:
        fail()
        del x
    y = x
    return y


def deferred_body(manager):
    with manager:
        def read():
            x = initial
            x = replacement
            return x
    return read


module_value = module_initial


def global_binding(manager):
    global module_value
    with manager:
        fail()
        module_value = replacement
        inside = module_value
    y = module_value
    return inside, y


class Base:
    def __init__(self):
        use_base()


class Child(Base):
    with manager:
        fail()

        def __init__(self):
            use_child()


def constructor():
    return Child()


def completed_handler_assignment(old, new):
    value = old
    try:
        work()
    except Error:
        value = new
        consume(value)
    return value


def rebound_exception_alias(old, new):
    error = old
    try:
        work()
    except Error as error:
        error = new
        consume(error)
    return error


def completed_bare_handler(old, new):
    value = old
    try:
        work()
    except:
        value = new
        consume(value)
    return value
