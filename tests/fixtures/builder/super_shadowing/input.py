class Parent:
    def method(self):
        return 1


class Child(Parent):
    def parameter(self, super):
        return super().method()

    def local(self):
        super = callback
        return super().method()

    def imported(self):
        from unknown import super
        return super().method()

    def module_shadow(self):
        return super().method()


def factory(callback):
    super = callback

    class Nested(Parent):
        def method(self):
            return super().method()

    return Nested()


super = callback


def main():
    return Child()


def read_custom_super_member(super):
    return super().run


class ImportedSuperChild(Parent):
    def direct_import(self):
        from builtins import super

        return super().method()

    def aliased_import(self):
        from builtins import super as native_super

        super = native_super
        return super().method()

    def conditional_import(self, flag, replacement):
        from builtins import super as native_super

        super = replacement
        return flag and ((super := native_super), super().method())
