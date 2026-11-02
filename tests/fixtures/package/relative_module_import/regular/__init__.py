from . import worker


def main():
    return worker.work()


def direct_member():
    return worker.value


from .subpkg import child as nested_child


def nested_call():
    return nested_child.work()
