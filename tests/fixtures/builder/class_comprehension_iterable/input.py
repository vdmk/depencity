values = module_values
module_result = [item for item in values]
eager_value = 1
eager_filter = True


def main(items):
    function_result = [item for item in items]
    return function_result


class C:
    values = class_values
    groups = class_groups
    unrelated_class_name = class_value
    result = [item for item in values]
    grouped = [item for group in groups for item in group]
    unrelated = [unrelated_class_name for item in values]
    direct_eager_value = eager_value
    list_eager_value = [eager_value for item in values]
    set_eager_value = {eager_value for item in values}
    dict_eager_value = {item: eager_value for item in values if eager_filter}
    filtered_eager_value = [item for item in values if eager_filter]
    lazy_generator_value = (eager_value for item in values)


eager_value = 2
eager_filter = False
