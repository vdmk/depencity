from worker import *
from external import Exposed as Public
from external import unused

__all__ = ["Public"]


def main(value: Public):
    return transform(value)


def local_annotation(value):
    from other import Public

    item: Public = value
    return item
