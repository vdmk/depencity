class Item:
    def __init__(self):
        initialize()

    def run(self):
        return item_source


class Base:
    Factory = Item

    class Nested:
        def __init__(self):
            initialize_nested()

        def run(self):
            return nested_source

    def ordinary(self):
        return method_source
