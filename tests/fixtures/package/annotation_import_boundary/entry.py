forward_alias_value: worker.Alias = source
forward_alias_result = forward_alias_value.run()
forward_facade_value: alias_facade.Alias = source
forward_facade_result = forward_facade_value.run()
forward_public_factory: type[api.NestedAlias] = source
forward_public_result = forward_public_factory().run()


from .worker import Worker as Direct
from .worker import Alias as DirectAlias
from .worker import AliasChain, NestedAlias
from .api import Worker as Public, NestedAlias as PublicNested
from . import api
from .facade import Worker as Indirect
from .chain import Worker as TwoHop
from .alias_facade import Alias
from . import facade
from . import alias_facade
from . import worker
from .unused_facade import Unused

unused: Unused
type Shape = Unused


def generic[T: Unused](value: T):
    return value


def main(value: Direct):
    return value.run()


def direct_alias(factory: type[DirectAlias]):
    obj = factory()
    return obj.run()


def direct_alias_instance(value: DirectAlias):
    return value.run()


def qualified_direct_alias(factory: type[worker.Alias]):
    obj = factory()
    return obj.run()


def indirect(value: Indirect):
    return value.run()


def two_hop(value: TwoHop):
    return value.run()


def qualified(value: facade.Worker):
    return value.run()


def aliased(value: Alias):
    return value.run()


def runtime_control():
    return Indirect().run()


def alias_chain(value: AliasChain):
    return value.run()


def nested_alias(factory: type[NestedAlias]):
    return factory().run()


def qualified_nested(value: worker.NestedAlias):
    return value.run()


def public_instance(value: Public):
    return value.run()


def public_constructor(factory: type[PublicNested]):
    return factory().run()


def qualified_public(value: api.Worker):
    return value.run()


def qualified_facade_constructor(factory: type[alias_facade.Alias]):
    return factory().run()


def qualified_facade_instance(value: alias_facade.Alias):
    return value.run()


def qualified_public_constructor(factory: type[api.NestedAlias]):
    return factory().run()


def qualified_facade_chain(factory: type[alias_facade.AliasChain]):
    obj = factory()
    return obj.run()


def qualified_facade_namespace(factory: type[alias_facade.Namespace.Alias]):
    return factory().run()


def qualified_facade_runtime():
    return alias_facade.Alias().run()


def public_module_instance(value: api.worker.Worker):
    return value.run()


def public_module_constructor(factory: type[api.worker.Worker]):
    return factory().run()


def public_module_nested(factory: type[api.worker.NestedAlias]):
    obj = factory()
    return obj.run()


def public_module_facade(factory: type[api.alias_facade.Alias]):
    return factory().run()


def inherited_instance(value: Direct.Item):
    return value.run()


def inherited_constructor(factory: type[Direct.Item]):
    return factory().run()


def inherited_qualified(factory: type[worker.Worker.Item]):
    obj = factory()
    return obj.run()


def inherited_public(value: api.Worker.Item):
    return value.run()


def generic_imported[Direct](value: Direct):
    return value.run()


def generic_factory[DirectAlias](factory: type[DirectAlias]):
    obj = factory()
    return obj.run()


def generic_module[worker](value: worker.Worker):
    return value.run()


def generic_capture[Direct](callback=lambda: Direct):
    return callback


def generic_callable[Direct]():
    def read():
        return Direct()
    return read()


from .factories import make, make_qualified, Factory
from . import factories


def returned_receivers():
    factory = make
    saved = factory()
    alias = saved
    return saved.run(), alias.run(), make().run(), factories.make().run(), make_qualified().run()


def returned_annotation_origin():
    class Worker:
        def run(self):
            return wrong_caller_type

    return make().run()


def returned_method_receiver(factory: Factory):
    saved = factory.make()
    return saved.run(), factory.make().run(), Factory().make().run()


def callable_value_control():
    saved = make
    return saved.run(), make.run()


def constructor_result_control():
    return Factory().run()


from .api import Worker as ExportedWorker


def exported_class_with_submodule(value: ExportedWorker.Item):
    return value.run()


import builtins
from builtins import type as ClassType


def builtin_type_aliases(qualified: builtins.type[Direct], aliased: ClassType[Direct]):
    return qualified().run(), aliased().run(), qualified.run(), aliased.run()


saved_worker = worker
saved_indirect_class = Indirect


def module_alias_factory(factory: type[saved_worker.Worker]):
    obj = factory()
    return obj.run()


def module_alias_instance(value: saved_worker.Worker):
    return value.run()


def saved_class_factory(factory: type[saved_indirect_class]):
    obj = factory()
    return obj.run()


class Registry:
    Alias = Direct
    FacadeAlias = Indirect


def class_member_alias(value: Registry.Alias):
    return value.run()


def class_member_factory(factory: type[Registry.Alias]):
    obj = factory()
    return obj.run()


def class_member_runtime_alias(value: Registry.FacadeAlias):
    return value.run()


def exported_class_member():
    return ExportedWorker.Item, api.Worker.Item


from .api import worker as public_worker


def reexported_module_factory(factory: type[public_worker.Worker]):
    obj = factory()
    return obj.run()


def reexported_module_instance(value: public_worker.Worker):
    return value.run()


from .api import namespace as hints, namespace_api


def namespace_instance(value: hints.models.Worker):
    return value.run()


def namespace_factory(factory: type[hints.models.Worker]):
    return factory().run()


def reexported_namespace_factory(factory: type[namespace_api.models.Worker]):
    return factory().run()
