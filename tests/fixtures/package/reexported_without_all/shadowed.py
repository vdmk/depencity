from .facade import (
    parameter_only,
    local_only,
    lambda_only,
    comprehension_only,
    nested_only,
    class_only,
    rebound_only,
    global_used,
    default_used,
)
import reexported_without_all.facade as shadowed_api


def read_parameter(parameter_only):
    return parameter_only


def read_local(value):
    local_only = value
    return local_only


def create_lambda():
    return lambda lambda_only: lambda_only


def read_comprehension(items):
    return [comprehension_only for comprehension_only in items]


def read_nested(value):
    nested_only = value

    def read():
        return nested_only

    return read()


def import_in_sibling():
    from .facade import sibling_only


def read_in_sibling(sibling_only):
    return sibling_only


class Capture:
    class_only = replacement_value
    saved = class_only


rebound_only = replacement_value
saved_rebound = rebound_only

from .facade import version_used as active
saved_version = active
from .facade import version_unused as active


def create_qualified_lambda():
    return lambda shadowed_api: shadowed_api.lambda_only()


def read_qualified_comprehension(items):
    return [shadowed_api.comprehension_only() for shadowed_api in items]


def read_global():
    global global_used
    return global_used


def read_nonlocal():
    from .facade import nonlocal_used

    def read():
        nonlocal nonlocal_used
        return nonlocal_used

    return read()


def read_default(default_used=default_used):
    return default_used
