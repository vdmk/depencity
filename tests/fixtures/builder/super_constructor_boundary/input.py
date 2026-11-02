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


class Child(Base):
    def main(self):
        ordinary = super().ordinary()
        obj = super().Factory()
        return ordinary, obj.run()

    def qualified_control(self):
        obj = Base.Factory()
        return obj.run()

    def aliased_factory(self):
        Factory = super().Factory
        obj = Factory()
        return obj.run()

    def nested_factory(self):
        obj = super().Nested()
        return obj.run()

    def aliased_nested_factory(self):
        Factory = super().Nested
        obj = Factory()
        return obj.run()

    def aliased_method(self):
        method = super().ordinary
        return method()

    def opposite_cell(self, flag, replacement):
        nonlocal __class__
        if flag:
            __class__ = replacement
        else:
            return super().ordinary()
        return super().ordinary()

    def opposite_super(self, flag, replacement):
        global super
        if flag:
            super = replacement
        else:
            return super().ordinary()
        return super().ordinary()
