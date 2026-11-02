match record:
    case {"key": value}:
        exported = value
    case {**remaining}:
        exported = remaining
