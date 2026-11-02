from .public import execute
from .facade import discarded_only
import reexported_without_all.facade as module_facade
from . import facade as relative_facade

discarded_only


def main():
    return execute()


def local_import():
    from .public import execute as local_execute
    from .facade import discarded_local

    discarded_local

    return local_execute()


def qualified_reexport():
    return module_facade.work()


def call_facade_alias():
    alias = module_facade
    return alias.alias_only()


def call_facade_alias_chain():
    first = module_facade
    second = first
    return second.chain_only()


def call_annotated_facade_alias():
    alias: object = module_facade
    return alias.annotated_only()


def call_plain_facade_alias():
    alias = module_facade
    return alias.plain_only()


def call_relative_facade_module():
    return relative_facade.relative_only()


def unrelated_scope(scope_alias):
    return scope_alias.scope_only()


def unrelated_alias_assignment():
    scope_alias = module_facade
    return None


def call_overwritten_facade(unknown):
    alias = module_facade
    alias = unknown
    return alias.overwritten_only()


def call_conditional_overwrite(flag, unknown):
    alias = module_facade
    if flag:
        alias = unknown
    return alias.conditional_only()


def call_conditional_control(flag, unknown):
    alias = module_facade
    if flag:
        unrelated = unknown
    return alias.conditional_control()


def call_after_bare_annotation():
    alias = module_facade
    alias: object
    return alias.annotated_after_bare()


def call_same_line_overwrite(unknown):
    alias = module_facade
    alias = unknown; return alias.same_line_only()


def call_conditional_restore(flag, unknown):
    alias = unknown
    if flag:
        alias = module_facade
    return alias.restored_only()


def call_rhs_before_write():
    alias = module_facade
    alias = alias.rhs_only()
    return alias


def call_restored_parameter(alias, flag):
    if flag:
        alias = module_facade
    return alias.parameter_restore_only()


def call_overwritten_after_restore(flag, unknown):
    alias = unknown
    if flag:
        alias = module_facade
    alias = unknown
    return alias.overwritten_restore_only()
