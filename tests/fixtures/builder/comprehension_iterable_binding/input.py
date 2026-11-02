def main(x, groups):
    same_name = [x for x in x]
    renamed_target = [item for item in x]
    unpacked = [first for (x, first, *rest) in x]
    later_iterable = [item for group in groups for item in group]
    later_shadow = [item for x in x for item in x]
    return same_name, renamed_target, unpacked, later_iterable, later_shadow


def capture_visible_value(items, first, second):
    value = first
    listed = [value for item in items]
    unique = {value for item in items}
    mapped = {item: value for item in items}
    nested = [[value for inner in items] for outer in items]
    deferred = (value for item in items)
    value = second
    return listed, unique, mapped, nested, deferred


def capture_walrus_order(items, first, second):
    value = first
    result = [(value, (value := item), value) for item in items]
    value = second
    return result


def preserve_later_target_shadow(items, outer):
    value = outer
    return [value for item in items if value for value in items]


module_value = 1
module_result = [module_value for item in module_items]
module_value = 2
