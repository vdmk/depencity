from builtins import list as source_module
from builtins import tuple as native_tuple


def main(value):
    return source_module(), source_module.work(value), native_tuple(value)


def qualified_module(value):
    import builtins.list

    return builtins.list(), builtins.list.work(value)


def namespace_module(value):
    from builtins import type as source_namespace

    return source_namespace(), source_namespace.worker.work(value)


class Worker:
    def run(self):
        return payload


def namespace_type_hint(factory):
    from builtins import type as SourceType

    factory: SourceType[Worker]
    return factory(), factory.run()
