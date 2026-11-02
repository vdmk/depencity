from . import worker
from .worker import REASSIGNED
from .worker import VALUE
from .worker import VALUE_ALIAS as ALIAS


def main():
    direct = VALUE
    aliased = ALIAS
    qualified = worker.VALUE
    reassigned = REASSIGNED
    deleted = worker.DELETED
    conditional = worker.CONDITIONAL
    rebound = worker.REBOUND
    return direct, aliased, qualified, reassigned, deleted, conditional, rebound
