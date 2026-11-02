def main(a, b, items, other):
    arithmetic = (a + b, a - b, a * b, a / b, a // b, a % b, a ** b, a @ b)
    bitwise = (a << b, a >> b, a & b, a | b, a ^ b)
    unary = (+a, -a, ~a, not a)
    comparisons = (
        a == b,
        a != b,
        a < b,
        a <= b,
        a > b,
        a >= b,
        a in items,
        a not in items,
        a is b,
        a is not b,
    )
    chained = a < b < other
    logic = a and b or other
    conditional = a if a > b else b
    accumulated = a
    accumulated += b
    return arithmetic, bitwise, unary, comparisons, chained, logic, conditional


def short_circuit_comparisons(a, b, c, old, new):
    three_way = old
    result = a < b < (three_way := new)
    three_way_after = three_way

    longer = old
    result = a < b < c < (longer := new)
    longer_after = longer

    first_operand = old
    result = (first_operand := new) < b < c
    first_operand_after = first_operand

    first_comparator = old
    result = a < (first_comparator := new) < c
    first_comparator_after = first_comparator

    explicit = old
    if a < b:
        explicit = new
    explicit_after = explicit

    and_form = old
    (a < b) and (and_form := new)
    and_form_after = and_form

    return (
        three_way_after,
        longer_after,
        first_operand_after,
        first_comparator_after,
        explicit_after,
        and_form_after,
    )


def middle_call_once(a, get_middle, c):
    return a < get_middle() < c


def middle_operand_uses(a, b, c):
    return a < b < c
