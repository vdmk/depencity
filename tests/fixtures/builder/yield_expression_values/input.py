from typing import Awaitable


def exchange(value):
    result = yield value
    return result


def pause():
    yield


def delegate(source):
    result = yield from source
    return result


def yield_before_final_return(value, replacement):
    try:
        yield value
        return value
    finally:
        return replacement


def delegate_before_final_raise(source):
    try:
        yield from source
    finally:
        raise RuntimeError


def yield_in_handler_and_else(value, action):
    try:
        action()
    except ValueError:
        yield value
    else:
        yield from value
    finally:
        yield value
        return


def yield_with_nested_finally(value):
    try:
        try:
            yield value
        finally:
            yield value
            return
    finally:
        return


def main(value, replacement, action):
    return (
        yield_before_final_return(value, replacement),
        delegate_before_final_raise(value),
        yield_in_handler_and_else(value, action),
        yield_with_nested_finally(value),
    )


def call_received_value(value):
    return (yield value)()


def call_delegated_result(source):
    return (yield from source)()


class Worker:
    def run(self):
        return payload


def receive_receiver():
    value = yield Worker()
    return value.run()


def annotated_received_receiver():
    value: Worker = yield Worker()
    return value.run()


def delegated_receiver(source: list[Worker]):
    value = yield from source
    return value.run()


async def await_receiver(pending: Awaitable[Worker]):
    value = await pending
    return value.run()


async def annotated_awaited_receiver(pending: Awaitable[Worker]):
    value: Worker = await pending
    return value.run()
