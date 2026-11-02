__class__ = module_value


class Replacement:
    pass


def replace(cls):
    return Replacement


@replace
class Original:
    @staticmethod
    def marker():
        return original_value

    def read(self):
        return __class__

    def nested(self):
        def read():
            return __class__

        return read()

    def alias(self):
        cls = __class__
        return cls.marker()

    def direct(self):
        return __class__.marker()

    def saved(self):
        member = __class__.marker
        return member()

    def construct(self):
        return __class__()

    def parameter_shadow(self, __class__):
        return __class__

    def enclosing_shadow(self, value):
        __class__ = value

        def read():
            return __class__

        return read()

    def global_shadow(self):
        global __class__
        return __class__


@unknown_decorator
class Uncertain:
    def read(self):
        return __class__


def main():
    return Original(), Uncertain()
