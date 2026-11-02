async def main(source):
    for sync_item in source:
        pass

    async for async_item in source:
        pass

    sync_items = [item for item in source]
    async_items = [item async for item in source]
    return sync_item, async_item, sync_items, async_items


def generator_setup(source, fallback):
    try:
        return (hidden(item) async for item in source)
    except Exception:
        return fallback


def delayed_generator(source, fallback):
    try:
        return (hidden(item) for group in source async for item in group)
    except Exception:
        return fallback
