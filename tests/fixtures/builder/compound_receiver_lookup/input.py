class namespace:
    class Worker:
        def run(self):
            return result


def main(items: list[namespace.Worker], index):
    return (
        items[index.value].run(),
        items[index.get()].run(),
        items[index.start:index.stop][0].run(),
        namespace.Worker().run(),
    )


def unresolved_receivers(items: list[namespace.Worker], index):
    return items[index.value].missing(), unknown_factory().run()


def select_subscript_receiver(
    values: list[namespace.Worker], fallback: namespace.Worker
):
    return (values[0] or fallback).run()
