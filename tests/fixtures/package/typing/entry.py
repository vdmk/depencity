import typing as api
from typing import Sequence as Container


class Worker:
    def run(self):
        return payload


def named(items: Container[Worker]):
    return items[0].run()


def qualified(items: api.Sequence[Worker]):
    return items[0].run()


def native(items: list[Worker]):
    return items[0].run()
