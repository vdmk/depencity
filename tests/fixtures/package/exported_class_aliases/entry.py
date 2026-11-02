from .worker import Exported, Chained, Container, Rebound, Extracted, Instance
from .facade import Forwarded
from . import worker


class Child(Exported):
    pass


class QualifiedChild(worker.Exported):
    pass


def main(value):
    direct = Exported(value)
    chained = Chained(value)
    forwarded = Forwarded(value)
    child = Child(value)
    qualified = QualifiedChild(value)
    nested = Container.Nested(value)
    local_alias = Exported
    local = local_alias(value)
    return (
        direct.method(),
        chained.method(),
        forwarded.method(),
        child.method(),
        qualified.method(),
        nested.method(),
        local.method(),
        worker.Exported(value).method(),
        Exported.method(direct),
        Exported.value,
    )


def use_annotation(value: Exported):
    return value.method()


def use_qualified_annotation(value: worker.Exported):
    return value.method()


def use_forwarded_annotation(value: Forwarded):
    return value.method()


def use_unknown():
    return Rebound(), Extracted(), Instance()


def construct_nested_receiver(value):
    return Container().Nested(value)
