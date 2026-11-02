from . import worker as worker_alias
from . import absent


def main():
    return worker_alias.work()


def missing_submodule():
    return absent.work()
