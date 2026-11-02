def factory():
    return None


class Child(factory):
    pass


def invoke(value: Child):
    return value.missing()


class Base:
    def method(self):
        return known


instance = Base()
instance_alias = instance
class_alias = Base


class InstanceChild(instance):
    pass


class InstanceAliasChild(instance_alias):
    pass


class ClassAliasChild(class_alias):
    pass


def main():
    return (
        InstanceChild().method(),
        InstanceAliasChild().method(),
        ClassAliasChild().method(),
    )
