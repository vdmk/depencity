from .worker import build_total
import internal_calls.worker as internal_calls


def main(items: list[int]) -> int:
    return build_total(items)


def aliased(items: list[int]) -> int:
    return internal_calls.build_total(items)
