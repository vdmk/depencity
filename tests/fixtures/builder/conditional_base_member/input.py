"""Snapshot discovered candidates without proving conditional method availability."""


class First:
    if enabled:
        def method(self):
            return first_value


class Second:
    def method(self):
        return second_value


class Last:
    def method(self):
        return last_value


class Child(First, Second, Last):
    pass


class Deleted:
    def method(self):
        return deleted_value

    if remove_method:
        del method


class DeletedChild(Deleted, Second, Last):
    pass


class Intermediate(First):
    pass


class NestedChild(Intermediate, Second, Last):
    pass


class Guaranteed(Second):
    if override_method:
        def method(self):
            return override_value


class GuaranteedChild(Guaranteed, Last):
    pass


Selected = First
if select_second:
    Selected = Second


class SelectedChild(Selected, Last):
    pass


def main():
    child = Child()
    deleted = DeletedChild()
    nested = NestedChild()
    guaranteed = GuaranteedChild()
    selected = SelectedChild()
    return (
        child.method(),
        deleted.method(),
        nested.method(),
        guaranteed.method(),
        selected.method(),
    )


if define_class:
    class GuardedOverride(Second):
        def method(self):
            return overridden_value

    class GuardedConditional(Second):
        if override_method:
            def method(self):
                return conditional_value

    class GuardedReassigned:
        member = first_value
        member = second_value
        saved = member


def guarded_members():
    return GuardedOverride().method(), GuardedConditional().method()
