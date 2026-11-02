def main(value, manager):
    with manager:
        del value
    guarded = value
    del value
    return guarded, value


def nested_guards(value, manager):
    try:
        with manager:
            class Clear:
                nonlocal value
                del value
    except Exception:
        pass
    return value


def deferred_body(manager):
    with manager:
        def clear(value):
            del value
            return value

    return clear


async def async_guard(value, manager):
    async with manager:
        del value
    return value


def finally_guard(value):
    try:
        pass
    finally:
        del value
    return value


def conditional_versions(value, other, flag, manager):
    if flag:
        value = other
    with manager:
        del value
    return value
