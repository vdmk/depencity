from .worker import Alias
from . import worker


def main():
    action = Alias
    return action()


def shared():
    action = Alias
    return action(action)


def method():
    ClassAlias = worker.A
    value = ClassAlias()
    return value.run()


def method_shared():
    ClassAlias = worker.A
    value = ClassAlias()
    return value.run(value.run)


def qualified():
    return worker.run()


def direct_import():
    return Alias()


def local(value=None):
    return local_payload


def dynamic(flag):
    action = Alias
    return (action if flag else local)(action)


def pass_callable():
    return consume(Alias)


def pass_declarations():
    return consume(worker.configured, worker.Derived)
