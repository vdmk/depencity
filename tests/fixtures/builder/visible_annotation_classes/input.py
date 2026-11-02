forward_alias_value: ForwardAlias = source
forward_alias_result = forward_alias_value.run()
forward_chain_value: ForwardChain = source
forward_chain_result = forward_chain_value.run()
forward_nested_value: ForwardNamespace.Inner = source
forward_nested_result = forward_nested_value.run()
forward_factory: type[ForwardChain] = source
forward_constructed_result = forward_factory().run()


class Worker:
    def run(self):
        return 1


# Ordinary data reads retain the earlier definition.
early_worker_result = Worker().run()
ReboundType = Worker


# Annotation hints may use the final type binding after redefinition/rebinding.
def repeated_definition_hint(value: Worker):
    return value.run()


def rebound_type_hint(value: ReboundType):
    return value.run()


class Worker:
    def run(self):
        return 2


ReboundType = Worker


class AlternateWorker:
    def run(self):
        return 3


WorkerAlias = AlternateWorker


def latest_class(value: Worker):
    return value.run()


def aliased_class(value: WorkerAlias):
    return value.run()


def local_class(value):
    class Worker:
        def run(self):
            return 4

    value: Worker
    return value.run()


def ambiguous_class(flag, value):
    if flag:
        class Choice:
            def run(self):
                return 5
    else:
        class Choice:
            def run(self):
                return 6

    value: Choice
    return value.run()


published_value: Published = source
published_result = published_value.run()


class PublishClass:
    global Published

    class Published:
        def run(self):
            return published_source


published_class = Published

future_nested: FutureNamespace.Worker = source
future_nested_result = future_nested.run()


class FutureNamespace:
    class Worker:
        def run(self):
            return nested_source


class Outer:
    class Inner:
        def run(self):
            return inner_source

    def body_hint(self, value):
        value: Inner
        return value.run()

    def qualified_body_hint(self, value):
        value: Outer.Inner
        return value.run()

    def signature_hint(self, value: Inner):
        return value.run()


def enclosing_function(value):
    class Captured:
        def run(self):
            return captured_source

    class Holder:
        def invoke(self, value):
            value: Captured
            return value.run()

    return Holder().invoke(value)


def global_annotation_scope():
    class MissingGlobal:
        def run(self):
            return wrong_enclosing_source

    def missing(value):
        global MissingGlobal
        value: MissingGlobal
        return value.run()

    class Worker:
        def run(self):
            return wrong_shadow_source

    def present(value):
        global Worker
        value: Worker
        return value.run()

    return missing, present


def nonlocal_annotation_scope():
    def middle():
        class Captured:
            def run(self):
                return nonlocal_source

        def inner(value):
            nonlocal Captured
            value: Captured
            return value.run()

        return inner

    return middle


def unbound_enclosing_annotation():
    Worker: object

    def inner(value):
        value: Worker
        return value.run()

    def nonlocal_inner(value):
        nonlocal Worker
        value: Worker
        return value.run()

    return inner, nonlocal_inner


ForwardAlias = AlternateWorker
ForwardChain = ForwardAlias
ForwardNamespace = Outer
