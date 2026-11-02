from . import worker, public
import module_self_reexport.absolute_worker as absolute
from .shadow import worker as shadowed
from .plain import worker as plain


def main():
    return worker.run()


def aliased():
    return public.run()


def absolute_import():
    return absolute.run()


def read_values():
    return worker.value, absolute.value


def package_member_shadow():
    return shadowed.run()


def no_reexport():
    return plain.run()


def absolute_shadowed_alias():
    import module_self_reexport.replaced.worker as selected

    return selected.run()


def intermediate_shadowed_alias():
    import module_self_reexport.intermediate.worker as selected

    return selected.run()
