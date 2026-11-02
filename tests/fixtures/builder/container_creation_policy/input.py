def list_comprehension(items):
    return [item for item in items]


def set_comprehension(items):
    return {item for item in items}


def dict_comprehension(items):
    return {item: item for item in items}


def synchronous_generator(items):
    return (item for item in items)


async def asynchronous_generator(items):
    return (item async for item in items)


def explicit_list_constructor(items):
    return list(items)


def direct_container_literals():
    return [1], {1}, {'item': 1}, (1,)
