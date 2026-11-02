def main(flag, old, replacement, check, report, nested):
    value = old
    assert check(flag), report((value := replacement), nested(value))
    message_value = value

    tested = old
    assert (tested := flag)
    return message_value, tested
