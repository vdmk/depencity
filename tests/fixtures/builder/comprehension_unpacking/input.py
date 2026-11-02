def main(groups):
    return [value for (first, *rest) in groups for value in rest]


def independent_operations(items, obj, left, right):
    attributes = [obj.attr for _ in items]
    arithmetic = [left + right for _ in items]
    indexed = [obj[0] for _ in items]
    containers = [[left, right] for _ in items]
    return attributes, arithmetic, indexed, containers


class Worker:
    def run(self):
        return payload


def typed_receiver(items, obj: Worker):
    return [obj.run() for _ in items]
