class A:
    def run(self):
        return 1

    def only_a(self):
        return 2


class B:
    def run(self):
        return 3


class C:
    pass


def main(
    value: A | B,
    optional: A | None,
    parenthesized: (A | B),
    partial: A | C,
):
    return (
        value.run(),
        optional.run(),
        parenthesized.run(),
        partial.only_a(),
    )


def union_element_boundary(
    values: list[A | B],
    optional: list[A | None],
    pair: tuple[A | B, ...],
    nested: list[list[A | B]],
    simple: list[A],
):
    saved = values[0]
    return (
        values[0].run(),
        saved.run(),
        optional[0].run(),
        pair[0].run(),
        nested[0][0].run(),
        simple[0].run(),
    )


def quoted_hints(named: "A", union: "A | B", generic: "list[A]"):
    return named.run(), union.run(), generic[0].run()
