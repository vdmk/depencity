class C:
    def method(self):
        return 1


class Registry:
    shared = C()
    annotated: C = unknown_instance
    elements: list[C] = unknown_elements


class InheritedRegistry(Registry):
    pass


def class_member_receivers():
    saved = Registry.shared
    annotated = Registry.annotated
    elements = Registry.elements
    return saved.method(), annotated.method(), elements[0].method(), Registry.shared.method()


def named_container_boundary():
    qualified = Registry.elements[0].method()
    elements = Registry.elements
    named = elements[0].method()
    return qualified, named


def class_member_annotation_origin():
    C = unrelated_type
    saved = Registry.annotated
    return saved.method(), C


def annotated_member_method_values():
    saved = Registry.annotated.method
    inherited = InheritedRegistry.annotated.method
    return saved(), inherited(), Registry.annotated.method()


class Left:
    @staticmethod
    def run():
        return left_source


class Right:
    @staticmethod
    def run():
        return right_source


def computed_receiver_boundary(flag):
    inline = (Left if flag else Right).run()
    selected = Left if flag else Right
    named = selected.run()
    constructed = Left().run()
    return inline, named, constructed


def annotated_class_elements(
    values: list[type[Left]],
    pair: tuple[type[Left], type[Right]],
    nested: list[list[type[Left]]],
):
    inline = values[0].run()
    saved = values[0]
    named = saved.run()
    pooled = pair[0].run()
    deep = nested[0][0].run()
    return inline, named, pooled, deep


class Replaced(C):
    method = 42


def replace(function, replacement=42):
    return replacement


@replace
def replaced():
    return 2


def keep(function):
    return function


@keep
def kept():
    return 3


def shadow_classmethod():
    def classmethod(function):
        return 42

    class Local:
        @classmethod
        def method(cls):
            return cls.make()

        @staticmethod
        def make():
            return 4

    return Local.method()


def shadow_staticmethod():
    def staticmethod(function):
        return 42

    class Local:
        @staticmethod
        def method():
            return 5

    return Local.method()


def main(obj: C, items: list[C], unique: set[C], frozen: frozenset[C]):
    saved = obj.method
    consume(obj.method)
    return (
        saved(),
        obj.method(),
        items[0].method(),
        unique[0].method(),
        frozen[0].method(),
        replaced(),
        kept(),
        shadow_classmethod(),
        shadow_staticmethod(),
        Replaced.method(),
    )


class Namespace:
    def method(self):
        def hidden():
            return local_payload

        return hidden

    class Nested:
        @staticmethod
        def visible():
            return nested_payload


def namespace_members():
    hidden = Namespace.method.hidden
    return hidden(), Namespace.method.hidden(), Namespace.Nested.visible()


def make_worker() -> C:
    return C()


def factory_receiver():
    saved = make_worker()
    return saved.method(), make_worker().method(), C().method()


def make_qualified() -> Namespace.Nested:
    return unknown_result


def make_quoted() -> "C":
    return unknown_result


@opaque
def make_decorated() -> C:
    return unknown_result


def hinted_receivers():
    factory = make_worker
    saved = factory()
    alias = saved
    return (
        alias.method(),
        make_qualified().visible(),
        make_quoted().method(),
        make_decorated().method(),
        factory.method(),
        consume(make_worker()).method(),
    )


def factory_annotation_origin():
    class C:
        def method(self):
            return wrong_caller_type

    return make_worker().method()


def make_union() -> C | Left:
    return unknown_result


def make_container() -> list[C]:
    return unknown_result


def make_generic[C]() -> C:
    return unknown_result


async def make_async() -> C:
    return unknown_result


def make_generator() -> C:
    yield unknown_result


def unsupported_factory_hints():
    return (
        make_union().method(),
        make_container()[0].method(),
        make_generic().method(),
        make_async().method(),
        make_generator().method(),
    )


def initialize_instance(self) -> Right:
    pass


class Constructed:
    __init__ = initialize_instance

    def run(self):
        return constructed_payload


def constructor_control():
    return Constructed().run()
