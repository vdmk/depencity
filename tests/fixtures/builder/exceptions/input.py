def parse_or_default(text, fallback):
    try:
        value = int(text)
        if value < 0:
            raise ValueError(text)
    except ValueError as error:
        value = fallback + len(str(error))
    except Exception:
        value = fallback
    finally:
        value += 1
    return value


def handle_group(errors):
    handled = errors
    try:
        raise ExceptionGroup('errors', errors)
    except* ValueError as error:
        handled = error
    except* TypeError as error:
        handled = error
    return handled


def cause_call(exc, replacement, factory):
    raise exc from factory(exc := replacement)


def attribute_cause(exc, replacement):
    raise exc.error from (exc := replacement)


def ordinary_cause(exc, cause):
    raise exc from cause


def main(receiver, fallback):
    try:
        receiver.field
    except AttributeError:
        recover(fallback)


def attribute_write(receiver, value):
    try:
        receiver.field = value
    except AttributeError:
        recover(value)


def subscript_control(items, index):
    try:
        items[index]
    except IndexError:
        recover(index)


async def await_task(task):
    try:
        await task
    except Exception:
        recover()


async def awaited_assignment(task, old):
    value = old
    try:
        value = await task
    except Exception:
        value = fallback
    return value


def eager_comprehension(items):
    try:
        [item.field for item in items]
    except AttributeError:
        recover()


def comprehension_forms(items):
    try:
        {item.field for item in items}
        {item.field: item.other for item in items}
        [[item.field for item in group] for group in items]
        [1 for item in items if check(item)]
    except Exception:
        recover()


def eager_class_body(receiver):
    try:
        class Capture:
            result = receiver.field
    except AttributeError:
        recover()


def deferred_body_control(items):
    try:
        def deferred():
            return hidden()

        callback = lambda: hidden()
        pending = (hidden(item) for item in items)
    except Exception:
        recover()


def eager_setup_control():
    try:
        def deferred(value=setup()):
            return hidden()

        pending = (hidden(item) for item in prepare())
    except Exception:
        recover()


async def await_exception_group(task):
    try:
        await task
    except* Exception:
        recover()


def delegated_generator(items):
    try:
        yield from items
    except Exception:
        recover()


def handler_type_order(work, original, replacement):
    value = original
    try:
        work()
    except ValueError:
        return value
    except (value := replacement):
        return value


def conditional_handler_type(work, original, replacement):
    value = original
    try:
        work()
    except (value := replacement):
        pass
    return value


def group_handler_type_order(work, original, replacement):
    value = original
    try:
        work()
    except* ValueError:
        first = value
    except* (value := replacement):
        second = value
    return value


def group_body_before_later_type(work, original, replacement, select):
    value = original
    try:
        work()
    except* ValueError:
        value = replacement
    except* select(value):
        consume(value)
    return value


def unpack_source(source, fallback):
    try:
        first, second = source
    except ValueError:
        return fallback
    return first, second


def unpack_call(factory, fallback):
    try:
        first, second = factory()
    except ValueError:
        return fallback
    return first, second


def ordinary_handler_type(work, original, replacement):
    handler = original
    try:
        work()
    except ValueError:
        handler = replacement
    except handler:
        recover()
    return handler


def missing_handler_type(work, replacement):
    try:
        work()
    except ValueError:
        handler = replacement
    except handler:
        recover()


def handler_type_expression_write(work, original, selected, replacement):
    handler = original
    try:
        work()
    except (handler := selected):
        handler = replacement
    except handler:
        recover()


def deferred_handler_type(work, original, replacement, final):
    handler = original

    def invoke():
        nonlocal handler
        try:
            work()
        except ValueError:
            handler = replacement
        except handler:
            recover()

    handler = final
    return invoke


def pick():
    return TypeError


try:
    work()
except ValueError:
    import unused_external as pick
except pick():
    pass


def group_pick():
    return TypeError


try:
    work()
except* ValueError:
    import used_external as group_pick
except* group_pick():
    pass


def sibling_handler_body(old, new):
    value = old
    try:
        work()
    except First:
        value = new
    except Second:
        consume(value)
    return value


def completed_type_expression(original, first):
    handler = original
    try:
        work()
    except (handler := first):
        pass
    except handler:
        recover()
    return handler
