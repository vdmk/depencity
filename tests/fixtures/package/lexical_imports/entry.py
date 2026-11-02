from .one import f as shared
from . import exported


def unrelated():
    from .two import f as shared
    return shared()


def unused_nested_import():
    from .two import f as shared
    return 0


def main():
    return shared()


def local_only():
    from .helper import f
    return f()


def shadowed(shared):
    return shared()


from . import one as api


class Saved:
    callback = api.f


from . import two as api
later_member = api.f
saved_member_call = Saved.callback()


def rebind_by_assignment(replacement):
    from . import one as module

    class Capture:
        callback = module.f

    module = replacement
    return Capture.callback(), module.f()


def reimport_with_comprehension(items):
    from . import one as module
    callbacks = [module.f for item in items]
    from . import two as module
    return callbacks, module.f()


def retain_saved_callable(replacement):
    from .one import f as action
    saved = action
    action = replacement
    return saved()


def reexport_control():
    return exported()


class LexicalUse:
    from .one import f

    result = f()


class AttributeUse:
    from .two import f


def class_imports():
    return LexicalUse.result, AttributeUse.f()


def retained_class_member():
    saved = LexicalUse.f
    return LexicalUse.f(), saved()


from .facade import Exposed


def reexported_class_member():
    return Exposed()


from . import facade


def qualified_exported_factory():
    return facade.ExposedFactory().run()
