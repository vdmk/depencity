class Worker:
    def __iter__(self):
        return iter([1, 2])

    def run(self):
        return 1


def main(values: Worker):
    direct = Worker()
    direct.run()

    for item in Worker():
        item.run()

    for annotated_item in values:
        annotated_item.run()

    first, second = Worker()
    first.run()

    head, *rest = Worker()
    rest.run()

    return [item.run() for item in Worker()]


def annotated_extraction_boundary(values: list[Worker]):
    indexed = values[0].run()
    saved = values[0]
    named = saved.run()

    for item in values:
        item.run()

    first, second = values
    first.run()
    head, *rest = values
    head.run()
    rest.run()

    eager = [element.run() for element in values]
    deferred = (element.run() for element in values)
    return indexed, named, eager, deferred


def calls_in_comprehensions(items, action):
    list_items = [action() for item in items]
    set_items = {action() for item in items}
    dict_items = {item: action() for item in items}
    nested_items = [action() for group in items for item in group if item]
    filtered_items = [item for item in items if action()]
    generator_items = (action() for item in items)
    return list_items, set_items, dict_items, nested_items, filtered_items, generator_items


async def async_calls_in_comprehension(items, action):
    return [action() async for item in items]


def non_call_comprehension_clauses(items, flag):
    return (
        [1 for item in items if flag],
        {1 for item in items if flag},
        {item: 1 for item in items if flag},
    )
