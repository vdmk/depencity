class Parent:
    def run(self):
        return base_payload


class Worker(Parent):
    def ordinary(self):
        return __class__.run(), super().run()

    def generic[T](self):
        return __class__.run(), super().run()

    def shadowed[__class__](self):
        return __class__.run()

    def shadowed_super[__class__](self):
        return super().run()

    def nested[__class__](self):
        def read():
            return __class__.run()
        return read()

    def parameter(self, __class__):
        return __class__.run(), super().run()

    def local(self):
        __class__ = replacement
        return __class__.run(), super().run()

    def explicit_global(self):
        global __class__
        return super().run()


class Generic[__class__](Parent):
    def ordinary(self):
        return __class__.run(), super().run()


def main(value: Worker):
    return value.shadowed(), value.shadowed_super()


class Alternative:
    @staticmethod
    def run():
        return alternative_payload


class ReboundCellWorker(Parent):
    def rebound(self):
        nonlocal __class__
        __class__ = Alternative
        return __class__.run(), super().run()

    def saved_rebound(self):
        nonlocal __class__
        before = __class__.run
        __class__ = Alternative
        after = __class__.run
        return before(), after()
