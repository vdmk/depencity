from .facade import Assigned, Imported, Long, Value, Container, Computed
from .cycle_a import Alias as Cycle


def main():
    return Assigned()


def import_alias():
    return Imported()


def long_alias():
    return Long()


def value_control():
    return Value()


def container_control():
    return Container()


def computed_control():
    return Computed()


def argument_control():
    return unknown(Assigned)


def cycle_control():
    return Cycle()


from .worker import call_captured


def initialized_export():
    return call_captured()
