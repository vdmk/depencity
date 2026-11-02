from . import worker
from .worker import Factory as Imported


def Factory(argument):
    return unknown_value


def main():
    value = Factory(worker)
    return value.run()


def other_argument():
    value = Factory(other)
    return value.run()


def keyword_argument():
    value = Factory(argument=worker)
    return value.run()


def member_argument():
    value = unknown(worker.value)
    return value.run()


def qualified_argument():
    value = unknown(worker.Factory)
    return value.run()


def imported_argument():
    value = unknown(Imported)
    return value.run()


def module_constructor():
    value = worker.Factory()
    return value.run()


def imported_constructor():
    value = Imported()
    return value.run()


def aliased_constructor():
    value = worker.value()
    return value.run()


def shared_input():
    value = worker.Factory(worker.Factory)
    return value.run()
