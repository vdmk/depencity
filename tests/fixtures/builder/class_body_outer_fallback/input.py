value = 1


class ReadsOuterBeforeLocal:
    before = value
    value = 2
    after = value

    def method(self):
        return value


class MissingOuter:
    unresolved = unknown_class_value


class ReplacedClass:
    pass


class ReplacedClass:
    same_name = ReplacedClass


class MissingClassName:
    unresolved = MissingClassName


class len:
    value = len([1])


class NestedClass:
    class Inner:
        pass

    class Inner:
        unresolved = NestedClass


def nested_class_factory(outer_value):
    class Outer:
        class Inner:
            value = outer_value

    return Outer


def local_shadow():
    before = value
    value = 3
    return before


before_constructor = Future.Container()
before_method = Future.run()


class Future:
    class Container:
        pass

    @staticmethod
    def run():
        return future_source


after_constructor = Future.Container()
after_method = Future.run()


class ClassBody:
    before_constructor = Late.Container()
    before_method = Late.run()

    class Late:
        class Container:
            pass

        @staticmethod
        def run():
            return class_source

    after_constructor = Late.Container()
    after_method = Late.run()


class ConditionalLocal:
    if enabled:
        value = 2
    saved = value


class LoopLocal:
    for value in items:
        pass
    saved = value


class DefiniteLocal:
    value = 2
    if enabled:
        value = 3
    saved = value


if enabled:
    class GuardedDefiniteLocal:
        value = 2
        saved = value

    class GuardedConditionalLocal:
        if other_enabled:
            value = 2
        saved = value


value = 3


def read_before_local(value):
    class Capture:
        before = value
        value = 2
        after = value

    return Capture.before, Capture.after


def read_conditional_local(value, enabled):
    class Capture:
        if enabled:
            value = 2
        saved = value

    return Capture.saved


def read_free_name(value):
    class Capture:
        saved = value

    return Capture.saved


def read_annotation_local(value):
    class Capture:
        value: object
        saved = value

    return Capture.saved


def read_method_free_name(value):
    class Capture:
        value = 2

        def read(self):
            return value

    return Capture


def read_comprehension_free_name(value, items):
    class Capture:
        value = 2
        saved = [value for item in items]

    return Capture.saved


def read_explicit_nonlocal(value):
    class Capture:
        nonlocal value
        before = value
        value = 2
        after = value

    return Capture.before, Capture.after


def read_explicit_global(value):
    class Capture:
        global value
        before = value
        value = 2
        after = value

    return Capture.before, Capture.after


def read_method_default(value):
    class Capture:
        def read(self, saved=value):
            return saved

        value = 2

    return Capture


def read_builtin_fallback(sum):
    class Capture:
        saved = sum([1])
        sum = 2

    return Capture.saved


def read_before_import(value):
    class Capture:
        saved = value
        from unavailable import replacement as value

    return Capture.saved
