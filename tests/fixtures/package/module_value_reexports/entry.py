from . import worker, import_facade, shadow, redirect
from .redirect import worker as Redirected
from .import_facade import Alias as Imported
from .import_facade import OtherAlias
from .assignment_facade import Alias as Assigned
from .bridge import Forward as Bridged
from .choice import Alias as Choice
from .cycle_a import Alias as Cyclic


def main():
    return Imported.value


def direct():
    Alias = worker
    return Alias.value


def assigned():
    return Assigned.value


def other_source():
    return OtherAlias.value


def bridged():
    return Bridged.value


def qualified():
    return import_facade.Alias.value


def shadowed():
    return shadow.worker.value


def redirected():
    return redirect.worker.value


def imported_redirect():
    return Redirected.value


def conditional():
    return Choice.value


def cyclic():
    return Cyclic.value


def assigned_namespace_reexport():
    from . import assignment_facade

    return assignment_facade.Alias.provide()


def saved_module_attribute():
    from . import import_facade

    alias = import_facade.Alias
    return alias.value
