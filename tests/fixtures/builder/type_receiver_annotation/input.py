import builtins
from builtins import type as ClassType


class Worker:
    @classmethod
    def build(cls):
        return result


class namespace:
    class Worker:
        @classmethod
        def build(cls):
            return nested_result


def main(
    factory: type[Worker],
    instance: Worker,
    qualified: type[namespace.Worker],
    union: type[Worker | namespace.Worker],
    missing: type[missing.Worker],
):
    return (
        factory.build(),
        factory(),
        instance(),
        qualified.build(),
        union.build(),
        missing.build(),
    )


def imported_type_shadow():
    from external import type

    def consume(factory: type[Worker]):
        return factory(), factory.build()

    return consume


def source_type_shadow():
    class type:
        pass

    def consume(factory: type[Worker]):
        return factory(), factory.build()

    return consume


def imported_builtin_type():
    from builtins import type

    def consume(factory: type[Worker]):
        return factory(), factory.build()

    return consume


def local_metadata_shadow(factory, type):
    factory: type[Worker]
    return factory(), factory.build()


def parameter_name_control(factory: type[Worker], type):
    return factory(), factory.build()


def builtin_type_aliases(qualified: builtins.type[Worker], aliased: ClassType[Worker]):
    return qualified(), aliased(), qualified.build(), aliased.build()


def shadowed_alias():
    class ClassType:
        pass

    def consume(factory: ClassType[Worker]):
        return factory(), factory.build()

    return consume


class Registry:
    factory: type[Worker] = source


def bound_class_factory():
    return Registry.factory(), Registry.factory.build()


def saved_class_factory():
    factory = Registry.factory
    return factory(), factory.build()


def bound_instance_factory(registry: Registry):
    return registry.factory(), registry.factory.build()


class TypeNamespace:
    type = shadowed_type
    del type

    @staticmethod
    def use(factory: type[Worker]):
        return factory()


class ContainerNamespace:
    list = shadowed_list
    del list

    @staticmethod
    def use(values: list[Worker]):
        return values[0].build()


def deleted_local_type(factory):
    type = shadowed_type
    del type
    factory: type[Worker]
    return factory()


builtin_namespace = builtins
next_namespace = builtin_namespace


def namespace_class_hint(factory: next_namespace.type[Worker]):
    return factory()


def namespace_container_hint(items: next_namespace.list[Worker]):
    return items[0].build()


AssignedType = ClassType


def assigned_class_hint(factory: AssignedType[Worker]):
    return factory()


def shadowed_assigned_type(factory):
    AssignedType = unrelated_type
    factory: AssignedType[Worker]
    return factory()


NativeType = type
NativeList = list


def native_class_hint(factory: NativeType[Worker]):
    return factory()


def native_container_hint(items: NativeList[Worker]):
    return items[0].build()


def quoted_class_hint(factory: type["Worker"], nested: type["namespace.Worker"]):
    return factory(), factory.build(), nested.build()


def quoted_union_class_hint(factory: type["Worker | namespace.Worker"]):
    return factory()


def replaced_qualified_type(factory):
    import builtins as metadata

    metadata.type = custom_type
    factory: metadata.type[Worker]
    return factory(), factory.build()


def captured_qualified_type(factory):
    import builtins as metadata

    factory: metadata.type[Worker]
    metadata.type = custom_type
    return factory(), factory.build()
