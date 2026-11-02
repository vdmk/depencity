def action():
    return action_payload


class Owner:
    supplied = supplied_action
    literal = None
    alias = action

    def declared(self):
        return method_payload


class Child(Owner):
    pass


def class_values():
    return Owner.supplied(), Owner.literal(), Owner.alias(), Owner.declared()


def inherited_value():
    return Child.supplied()


def annotated_receiver(receiver: Owner):
    return receiver.supplied()


def saved_value():
    saved = Owner.supplied
    return saved()


def overwritten_member(replacement):
    Owner.supplied = replacement
    return Owner.supplied()


class SuperChild(Owner):
    def supplied_value(self):
        return super().supplied()

    def aliased_value(self):
        return super().alias()

    def declared_method(self):
        return super().declared()


class MultipleBases(Owner, unknown_base):
    def unresolved_super(self):
        return super().supplied()


class ConfiguredMethod:
    def method(self, value=method_default):
        return method_payload


def call_configured_method():
    return ConfiguredMethod.method()


class InheritedConfiguredMethod(ConfiguredMethod):
    def invoke(self):
        return super().method()
