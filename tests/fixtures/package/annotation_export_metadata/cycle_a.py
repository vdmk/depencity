from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cycle_b import Ghost


def identity(value: Ghost):
    return value
