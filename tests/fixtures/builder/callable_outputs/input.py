async def worker(value):
    await discard(value)
    await discard_again(value)
    return 1


async def caller(value):
    await worker(value)
    return await worker(value)


def values(value):
    yield value


def consume():
    return values(1)
