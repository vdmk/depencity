class Control:
    def run(self):
        return control_source


class Example:
    global Example
    Example = replacement

    def run(self):
        return example_source


class Outer:
    class Inner:
        global Outer
        Outer = replacement

    def run(self):
        return outer_source


class Holder:
    class Nested:
        global Nested
        Nested = replacement


def nonlocal_class():
    Local = original

    class Local:
        nonlocal Local
        Local = replacement

        def run(self):
            return local_source

    return Local().run()


class Publisher:
    global published
    published = Control


def main():
    Alias = Example
    return Alias().run(), Outer().run(), published().run(), Nested()
