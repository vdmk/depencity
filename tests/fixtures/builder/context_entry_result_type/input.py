class Result:
    def run(self):
        return 1


class Manager:
    def __enter__(self):
        return Result()

    def __exit__(self, *args):
        pass

    def run(self):
        return 2


class SelfManager:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def run(self):
        return 3


class AsyncManager:
    async def __aenter__(self):
        return Result()

    async def __aexit__(self, *args):
        pass

    def run(self):
        return 4


def main():
    with Manager() as entered:
        first = entered.run()
    with SelfManager() as self_entered:
        second = self_entered.run()
    normal = Manager()
    third = normal.run()
    return first, second, third


async def async_main():
    async with AsyncManager() as entered:
        return entered.run()
