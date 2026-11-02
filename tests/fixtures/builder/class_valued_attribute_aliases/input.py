class Item:
    def __init__(self):
        initialize_item()

    def run(self):
        return item_source


class Box:
    Factory = Item
    value = opaque
    instance = Item()

    class Nested:
        def run(self):
            return nested_source


def main():
    Direct = Item
    Alias = Box.Factory
    Saved = Alias
    Nested = Box.Nested
    direct = Direct()
    aliased = Alias()
    saved = Saved()
    nested = Nested()
    return direct.run(), aliased.run(), saved.run(), nested.run()


def nonclass_controls():
    Value = Box.value
    Instance = Box.instance
    return Value(), Instance()
