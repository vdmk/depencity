class Target:
    def run(self):
        return outer_payload


def local_class(value):
    value: Target

    class Target:
        def run(self):
            return local_payload

    return value.run()


def annotated_assignment(value):
    result: Target = value

    class Target:
        def run(self):
            return assignment_payload

    return result.run()


def local_alias(value):
    value: Alias

    class Target:
        def run(self):
            return alias_payload

    Alias = Target
    return value.run()


def declaration_only(value):
    value: Target
    Target: object
    return value.run()


def unknown_local(value):
    value: Target
    Target = unknown
    return value.run()


def late_container_alias(values):
    values: Container[Target]
    Container = list
    return values[0].run()


def late_class_object_alias(factory):
    factory: Factory[Target]
    Factory = type
    value = factory()
    return value.run()


def visible_wrapper_aliases(values, factory):
    Container = list
    Factory = type
    values: Container[Target]
    factory: Factory[Target]
    value = factory()
    return values[0].run(), value.run()
