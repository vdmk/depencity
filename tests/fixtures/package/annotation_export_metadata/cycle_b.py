from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cycle_a import Ghost


def identity(value: Ghost):
    return value
