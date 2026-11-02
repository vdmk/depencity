class A:
    def method(self):
        return known


class Before(A):
    pass


def main(A):
    class ParameterChild(A):
        pass

    value = ParameterChild()
    return value.method()


A = unknown_base


class After(A):
    pass


class AliasBase:
    def method(self):
        return known_alias


Alias = AliasBase


class AliasChild(Alias):
    pass


def use_before():
    value = Before()
    return value.method()


def use_after():
    value = After()
    return value.method()


def use_alias():
    value = AliasChild()
    return value.method()


def local_shadow():
    class LocalBase:
        def method(self):
            return known_local

    LocalBase = unknown_local_base

    class LocalChild(LocalBase):
        pass

    value = LocalChild()
    return value.method()


class KeywordBase:
    def method(self):
        return keyword_result


class KeywordChild(KeywordBase, metaclass=(KeywordBase := type)):
    def inherited(self):
        return super().method()


class namespace:
    class Base:
        def method(self):
            return qualified_result


class QualifiedChild(namespace.Base, metaclass=(namespace := type)):
    pass


def use_captured_bases():
    return KeywordChild().method(), KeywordChild().inherited(), QualifiedChild().method()
