def main(a, b, c, d):
    and_three = a and b and (saved_and_three := c)
    and_four = a and b and c and (saved_and_four := d)
    or_three = a or b or (saved_or_three := c)
    or_four = a or b or c or (saved_or_four := d)
    nested = a and (b or (saved_nested := transform(c)))
    calls = a or transform(b) or (saved_call := transform(c))
    return (
        and_three,
        and_four,
        or_three,
        or_four,
        nested,
        calls,
        saved_and_three,
        saved_and_four,
        saved_or_three,
        saved_or_four,
        saved_nested,
        saved_call,
    )
