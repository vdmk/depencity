from .base import Base


class Worker(Base):
    def run(self):
        return actual_source


Alias = Worker
AliasChain = Alias


class Outer:
    class Inner:
        def run(self):
            return nested_source


Nested = Outer.Inner
NestedAlias = Nested
