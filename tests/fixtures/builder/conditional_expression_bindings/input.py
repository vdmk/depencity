def main(flag, old, new, left, right):
    statement_and = old
    if flag:
        statement_and = new

    expression_and = old
    flag and (expression_and := new)

    statement_or = old
    if not flag:
        statement_or = new

    expression_or = old
    flag or (expression_or := new)

    if flag:
        statement_choice = left
    else:
        statement_choice = right

    (expression_choice := left) if flag else (expression_choice := right)

    nested_choice = (
        ((nested_true := left) if flag else (nested_false := right))
        if old
        else ((nested_other_true := right) if flag else (nested_other_false := left))
    )

    and_statement_consumer = statement_and
    and_expression_consumer = expression_and
    or_statement_consumer = statement_or
    or_expression_consumer = expression_or
    if_statement_consumer = statement_choice
    if_expression_consumer = expression_choice
    return (
        and_statement_consumer,
        and_expression_consumer,
        or_statement_consumer,
        or_expression_consumer,
        if_statement_consumer,
        if_expression_consumer,
        nested_choice,
    )
