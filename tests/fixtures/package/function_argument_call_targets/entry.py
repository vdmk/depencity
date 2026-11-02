from .worker import extra, helper, passed, retain_type_default
from . import worker


def main():
    return helper(passed, extra=extra)


def pass_generic():
    return helper(retain_type_default)


def literal_callee():
    return (0)(worker.passed)
