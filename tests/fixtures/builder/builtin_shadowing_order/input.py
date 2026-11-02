module_before = len(items)
len = custom
module_after = len(items)


class C:
    class_before = sum(items)
    sum = custom
    class_after = sum(items)


def main(items):
    value = max(items)
    max = custom
    return value


def imported_shadow(items):
    value = len(items)
    import custom as len
    return value


def from_import_shadow(items):
    value = max(items)
    from custom import transform as max
    return value


def imported_shadow_with_outer(items):
    def len(values):
        return values

    def inner():
        value = len(items)
        import custom as len
        return value

    return inner()


def imported_shadow_before_and_after(items):
    before = len(items)
    import custom as len
    after = len(items)
    return before, after


def custom_length(items):
    return 0


before_conditional = min(items)
if enabled:
    min = custom_length
after_conditional = min(items)


class ConditionalBuiltin:
    before = abs(items)
    if enabled:
        abs = custom_length
    after = abs(items)


before_conditional_import = sorted(items)
if enabled:
    from external import operation as sorted
after_conditional_import = sorted(items)


class ConditionalImportedBuiltin:
    before = round(items)
    if enabled:
        from external import operation as round
    after = round(items)


def conditional_local(items, enabled):
    if enabled:
        max = custom_length
    return max(items)
