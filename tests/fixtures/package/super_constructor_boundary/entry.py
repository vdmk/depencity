from .base import Base


class Child(Base):
    def main(self):
        ordinary = super().ordinary()
        obj = super().Factory()
        return ordinary, obj.run()

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

    def qualified_control(self):
        obj = Base.Factory()
        return obj.run()
