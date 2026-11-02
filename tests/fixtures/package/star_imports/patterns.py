source = {}

match source:
    case {"outer": {"value": nested_value, **nested_rest}, **rest}:
        pass
    case {"private": private_value, **_private_rest}:
        pass
