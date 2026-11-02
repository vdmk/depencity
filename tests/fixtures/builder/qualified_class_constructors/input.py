class Direct:
    def __init__(self):
        initialize_direct()

    def run(self):
        return direct_source


class Base:
    def __init__(self):
        initialize_base()

    def run(self):
        return inherited_source


class Outer:
    class Inner:
        def __init__(self):
            initialize_nested()

        def run(self):
            return nested_source

    class Inherited(Base):
        pass

    class Plain:
        def run(self):
            return plain_source

    @staticmethod
    def ordinary():
        return ordinary_source


def main():
    direct = Direct()
    nested = Outer.Inner()
    inherited = Outer.Inherited()
    plain = Outer.Plain()
    ordinary = Outer.ordinary()
    return (
        direct.run(),
        nested.run(),
        inherited.run(),
        plain.run(),
        Outer.Inner().run(),
        ordinary.run(),
    )
