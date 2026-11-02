def main(x, replacement, mapping):
    value_then_rebind = {"first": (x := replacement), x: 0}
    read_then_rebind = {"first": x, "second": (x := replacement)}
    walrus_key = {(x := replacement): x}
    multiple_entries = {
        "first": (x := replacement),
        "second": x,
        "third": (x := replacement),
        "fourth": x,
    }
    unpack_then_read = {**(mapping := merge(x)), mapping["key"]: 0}
    read_then_unpack = {mapping["key"]: 0, **(mapping := merge(x))}
    return (
        value_then_rebind,
        read_then_rebind,
        walrus_key,
        multiple_entries,
        unpack_then_read,
        read_then_unpack,
    )
