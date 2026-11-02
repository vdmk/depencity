from __future__ import annotations

from dataclasses import dataclass
import unused_module


GLOBAL_TOTAL = 0


@dataclass
class Record:
    value: int
    label: str = "value"


def main(items: list[int], flag: bool = True) -> dict[str, int]:
    global GLOBAL_TOTAL
    running: int = 0
    record = Record(items[0] if items else 0)
    record.value += 1
    doubled = [item * 2 for item in items if item > 0]
    unique = {item for item in doubled}
    squares = {item: item * item for item in unique}
    sequence = (item + 1 for item in doubled)

    def bump() -> int:
        nonlocal running
        running += 1
        return running

    transform = lambda value: value + bump()
    if flag:
        running = sum(doubled)
    else:
        running += 1

    for item in sequence:
        running += transform(item)
    while running < 3:
        running += 1

    try:
        if (count := len(squares)) == 0:
            raise ValueError("empty")
    except ValueError as error:
        record.label = str(error)
        count = 0

    with open("input.txt") as handle:
        text = handle.read()
    assert running >= 0, text
    GLOBAL_TOTAL = running
    return {"total": running, "count": count, "first": record.value}
