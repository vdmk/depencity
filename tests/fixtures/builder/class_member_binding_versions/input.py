from __future__ import annotations


def forward_consumer(value: ForwardAliased):
    return value.alias(), value.chained(), value.run()


class ForwardAliased:
    def run(self):
        return forward_method

    alias = run
    chained = alias


class C:
    def method(self):
        return first_method

    def method(self):
        return replacement_method


class Aliased:
    def run(self):
        return aliased_method

    alias = run
    chained = alias


class InheritedAlias(Aliased):
    pass


class OverwrittenAlias(Aliased):
    alias = unknown


class Replaced:
    def method(self):
        return obsolete_method

    method = unknown


class Base:
    def inherited(self):
        return base_method


class Inherited(Base):
    pass


class DeletedInherited(Base):
    def inherited(self):
        return obsolete_override

    del inherited


class DeletedOwn:
    def method(self):
        return deleted_method

    del method


class Conditional:
    def method(self):
        return conditional_method

    if flag:
        method = unknown


class Constructed:
    def __init__(self, value):
        self.value = old_init

    def __init__(self, value):
        self.value = new_init


def main(obj: C, replaced: Replaced, aliased: Aliased):
    saved = aliased.alias
    return (
        C.method(),
        obj.method(),
        Replaced.method(),
        replaced.method(),
        Inherited.inherited(),
        DeletedInherited.inherited(),
        DeletedOwn.method(),
        Conditional.method(),
        Constructed(1),
        aliased.alias(),
        saved(),
    )


def call_alias_variants(obj: InheritedAlias, overwritten: OverwrittenAlias):
    return obj.alias(), obj.chained(), overwritten.alias()
