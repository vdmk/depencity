from .helper import f
from .helper import f as stable
from .helper import work


early = f()
f = external
later = f()


def unchanged():
    return stable()


def main():
    return f()


def replaced_export():
    return work()


def local_replacement():
    f = external
    return f()


def repeated_from_alias():
    from .helper import work as selected, f as selected
    return selected()


def repeated_module_alias():
    from . import helper as selected, helper as selected
    return selected.f()


def repeated_absolute_alias():
    import reassigned_import.helper as selected, reassigned_import.helper as selected
    return selected.f()


def repeated_unknown_alias():
    from .helper import f as selected, work as selected
    return selected()


def repeated_dotted_root():
    import reassigned_import.helper, reassigned_import.entry
    return reassigned_import.helper.f()
