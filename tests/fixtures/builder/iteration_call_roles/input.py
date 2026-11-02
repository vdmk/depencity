def action():
    return payload


def main(items):
    return [unknown() for x in [item for item in items]]


def known(items):
    return [action() for x in [item for item in items]]


def generators(items):
    return (unknown() for x in (item for item in items))


def mixed_iteration(items):
    return [unknown(x) for x in (item for item in items)]


def plain_iterable(items):
    return [unknown() for x in items]


def shared_endpoint(action):
    return [action(action) for item in action]


def replaced_target(callbacks):
    callback = action
    for callback in callbacks:
        callback()
    return callback()


def guarded_target(flag, callbacks):
    callback = action
    if flag:
        for callback in callbacks:
            callback()
    return callback()


def unpacked_target(callbacks):
    callback = action
    for _, callback in callbacks:
        callback()
    return callback()


async def async_target(callbacks):
    callback = action
    async for callback in callbacks:
        callback()
    return callback()


def reused_comprehension_target(groups):
    return [item for item in groups for item in item]
