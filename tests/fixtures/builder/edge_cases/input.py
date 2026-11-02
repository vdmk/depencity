import duplicate_module
import duplicate_module


global_obj = None


def main(groups, value):
    declared: int
    nested = [
        item
        for group in groups
        for item in group
        if item > 0
    ]
    with open("input.txt"):
        pass
    try:
        if value:
            return nested
        return []
    except:
        return []


def nested_returns(flag):
    if flag:
        if flag:
            return 1
        else:
            return 2
    else:
        return 3


def bare_return():
    return


def unusual_targets(obj, value):
    obj.field: int
    first, obj.field = value
    for obj.field in value:
        pass
    with manager() as obj.field:
        pass
    make_object().field = value
    obj[value].field = value
    del make_object().field
    make_object().field += value
    with None:
        pass
    assert value, value
    try:
        raise ValueError(value)
    except:
        raise
    error = ValueError(value)
    raise error
    raise ValueError(value) from value


def dynamic_attribute_read():
    return make_object().field


def global_attribute_write(value):
    global global_obj
    global_obj.field = value


def deep_nonlocal():
    value = 0

    def middle():
        def inner():
            nonlocal value
            value = 1
            return value

        return inner()

    return middle()


class State:
    def update(self, value):
        self.value = value
        self.value += value
        return self.value


def keyword_only(*, value):
    return value


def literal_subscript(value):
    return [1, 2][0] + {"value": value}["value"]


def finally_overrides_return():
    try:
        return original
    finally:
        return replacement


def finally_nested_return():
    try:
        return original
    finally:
        try:
            return replacement
        finally:
            pass


def finally_try_star_raises(first, failure):
    try:
        return first
    finally:
        try:
            pass
        except* ValueError:
            pass
        finally:
            raise failure


def finally_with_return(first, replacement):
    try:
        return first
    finally:
        with manager():
            return replacement


def finally_conditional_return(flag):
    try:
        return original
    finally:
        if flag:
            return replacement


def finally_raises():
    try:
        return original
    finally:
        raise failure


def finally_completes_normally():
    try:
        return original
    finally:
        cleanup()


def finally_rebinds_return(old, replacement):
    value = old
    try:
        return value
    finally:
        value = replacement


def finally_mutates_return(old, replacement):
    value = old
    try:
        return value
    finally:
        value.field = replacement


def finally_rebinds_then_mutates_return(old, replacement, extra):
    value = old
    try:
        return value
    finally:
        value = replacement
        value.child.field = extra


def finally_nested_mutates_return(old, replacement):
    value = old
    try:
        return value
    finally:
        value.child.field = replacement


def call_finally_cases(flag):
    return (
        finally_overrides_return(),
        finally_nested_return(),
        finally_try_star_raises(old, failure),
        finally_with_return(old, replacement),
        finally_nested_with_return(old, replacement),
        finally_suppressed_exception(old, replacement),
        finally_conditional_return(flag),
        finally_raises(),
        finally_completes_normally(),
        finally_rebinds_return(old, replacement),
        finally_mutates_return(old, replacement),
        finally_rebinds_then_mutates_return(old, replacement, extra),
        finally_nested_mutates_return(old, replacement),
    )


def finally_nested_with_return(first, replacement):
    try:
        return first
    finally:
        with manager():
            with manager():
                return replacement


def finally_suppressed_exception(first, replacement):
    try:
        return first
    finally:
        with manager():
            risky()
            return replacement
