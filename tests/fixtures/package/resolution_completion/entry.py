from .a_worker import action, Worker
from .c_facade import FunctionAlias as ForwardFunction, FactoryAlias as ForwardFactory, StaticAlias as ForwardStatic
from .x_facade import FunctionAlias as ReverseFunction, FactoryAlias as ReverseFactory, StaticAlias as ReverseStatic


def local_action():
    return local_payload


def main():
    return local_action()


def direct_function():
    return action()


def forward_function():
    return ForwardFunction()


def reverse_function():
    return ReverseFunction()


def direct_constructor():
    obj = Worker()
    return obj.run()


def forward_constructor():
    obj = ForwardFactory()
    return obj.run()


def reverse_constructor():
    obj = ReverseFactory()
    return obj.run()


def forward_static():
    return ForwardStatic()


def reverse_static():
    return ReverseStatic()


def nested_constructor():
    from .workers import Worker

    return Worker().run()


def saved_forward_member():
    from . import c_facade

    saved = c_facade.StaticAlias
    return saved()


def saved_reverse_member():
    from . import x_facade

    saved = x_facade.StaticAlias
    return saved()
