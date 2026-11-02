def main(items, groups, seed):
    empty_value = seed
    empty_result = [(empty_value := item) for item in []]
    after_empty = empty_value

    filtered_value = seed
    filtered_result = [
        (filtered_value := item) for item in items if False
    ]
    after_filtered = filtered_value

    multiple_value = seed
    multiple_result = [
        (multiple_value := inner)
        for group in groups
        for inner in group
    ]
    after_multiple = multiple_value

    set_value = seed
    set_result = {(set_value := item) for item in items}
    after_set = set_value

    dict_value = seed
    dict_result = {(dict_value := item): item for item in items}
    after_dict = dict_value

    nested_value = seed
    nested_result = [
        [(nested_value := inner) for inner in group]
        for group in groups
    ]
    after_nested = nested_value

    deferred_value = seed
    generator = ((deferred_value := item) for item in items)
    after_generator = deferred_value

    return (
        after_empty,
        after_filtered,
        after_multiple,
        after_set,
        after_dict,
        after_nested,
        after_generator,
    )
