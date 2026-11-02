__class__ = module_value


def main():
    __class__ = other
    ordinary = ordinary_value

    class A:
        def explicit(self):
            nonlocal __class__
            return __class__

        def plain(self):
            return __class__

        def normal_nonlocal(self):
            nonlocal ordinary
            return ordinary

        def parameter(self, __class__):
            return __class__

        def local(self):
            __class__ = local_value
            return __class__

        def explicit_global(self):
            global __class__
            return __class__

        def nested(self):
            def read():
                nonlocal __class__
                return __class__
            return read()

        def enclosing_local(self):
            __class__ = local_value
            def read():
                nonlocal __class__
                return __class__
            return read()

        def rebound(self):
            nonlocal __class__
            before = __class__
            __class__ = replacement
            return before, __class__

    return A


class NoOuter:
    def explicit(self):
        nonlocal __class__
        return __class__

    def plain(self):
        return __class__


class NestedOwner:
    def create(self, replacement):
        class Inner:
            nonlocal __class__
            __class__ = replacement
            value = __class__

        return Inner

    def create_shadowed(self, __class__, replacement):
        class Inner:
            nonlocal __class__
            __class__ = replacement
            value = __class__

        return Inner
