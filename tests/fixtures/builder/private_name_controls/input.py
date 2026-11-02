__token = module_payload


def __module_function():
    return __token


class Base:
    def __len__(self):
        return dunder_payload


class Child(Base):
    def read_class(self):
        return __class__


class ___:
    value = __token

    def __run(self):
        return unmangled_payload


def main():
    obj = Child()
    ordinary = ___()
    return obj.__len__(), ordinary.__run(), __module_function()


class Imported:
    import __external.child as public_module

    value = public_module


class FromImported:
    from __external.child import value

    result = value


class PatternReader:
    def read(self, subject):
        match subject:
            case Imported(__value=value):
                return value


class Bounded[T: __token]:
    pass


class Defaulted[T = __token]:
    pass


class KeywordLabels:
    value = action(__hidden=source)

    def invoke(self):
        return action(__option=source)

    class Nested(__setting=source):
        pass


class PrivateNames:
    def __init__(self, __value):
        self.__value = __value
        self._PrivateNames__value = explicit_value

    def __read(self):
        return self.__value

    def _PrivateNames__read(self):
        return self._PrivateNames__value

    def read_both(self):
        return self.__read(), self._PrivateNames__read()
