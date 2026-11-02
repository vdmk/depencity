def main(manager):
    try:
        with manager:
            pass
    except Exception:
        recover()


def bound_entry(manager):
    try:
        with manager as value:
            pass
    except Exception:
        recover()


async def unbound_async_entry(manager):
    try:
        async with manager:
            pass
    except Exception:
        recover()


async def bound_async_entry(manager):
    try:
        async with manager as value:
            pass
    except Exception:
        recover()
