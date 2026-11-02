from .facade import Assigned


def main(value):
    Assigned.field: int = value
    Assigned[value]: int = value
