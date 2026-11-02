from . import worker
from . import aliased_worker as public

from . import intermediate


class ReplacementWorker:
    @staticmethod
    def run():
        return replacement_payload


class ReplacementMiddle:
    worker = ReplacementWorker


intermediate = ReplacementMiddle
