from . import worker


def main():
    return worker.work()


import relative_module_shadow as package


def qualified_shadow():
    return package.work()


def saved_shadow():
    action = package.work
    return action()
