from .annotations import *

from_annotations = Public

from .control import *

from_control = Public


def main():
    return from_annotations, from_control


from .provider import Worker as IndirectWorker
from .types import Worker as DirectWorker
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cycle_a import Ghost


def metadata_only(value: IndirectWorker) -> IndirectWorker:
    return value


def cyclic_metadata(value: Ghost):
    return value


def resolved_metadata(value: DirectWorker):
    return value.run()
