async def main(source):
    async with acquire(source) as stream:
        async for item in stream:
            if item:
                await consume(item)
                continue

    async_items = [item async for item in source if item]
    sync_items = [item for item in source if item]
    async_stream = (item async for item in source if item)
    async_then_sync = [part for group in source async for part in group if part]
    sync_then_async = [part async for group in source for part in group if part]

    def values():
        for value in source:
            yield value
        yield
        yield from source

    return [value async for value in values()]


async def read_attribute(obj):
    return await obj.attr


def collect_attributes(items):
    return [item.value for item in items]


async def call_awaited_value(value):
    return (await value)()


def call_comprehension(items):
    return (item for item in items)()
