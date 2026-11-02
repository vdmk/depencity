from .worker import Worker, Outer


def make() -> Worker:
    return external_result


def make_qualified() -> Outer.Inner:
    return external_result


def initialize(self) -> Worker:
    pass


class Factory:
    __init__ = initialize

    def make(self) -> Worker:
        return external_result
