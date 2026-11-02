from unavailable_graph_library import my_func as f
from unavailable_graph_library import my_func as g
from unavailable_graph_library import run as run_direct
from unavailable_graph_argument import value
import unavailable_graph_library as api
import unavailable_graph_library.nested as nested
import unavailable_graph_library.nested
import unavailable_graph_alternative as alternative_api


def first():
    from unavailable_graph_one import run as same
    return same()


def second():
    from unavailable_graph_two import run as same
    return same()


def main():
    f(first)
    g(value)
    f(value)
    api.run()
    run_direct()
    nested.run()
    unavailable_graph_library.nested.run()
    first()
    second()


def replace_member(replacement):
    api.run = replacement
    return api.run()


def delete_member():
    del api.run
    return api.run()


def call_before_write(replacement):
    before = api.run()
    api.run = replacement
    return before, api.run()


def write_other_member(replacement):
    api.other = replacement
    return api.run()


def rebind_after_write(replacement):
    import unavailable_graph_library as local_api
    local_api.run = replacement
    local_api = unknown_api
    return local_api.run()


def guarded_module_alias(flag):
    if flag:
        alias = api
        chained = alias
        return alias.run(), chained.run()


def guarded_alias_rebinding(flag, replacement):
    if flag:
        alias = api
    alias = replacement
    return alias.run()


def guarded_alias_member_write(flag, replacement):
    if flag:
        alias = api
        alias.run = replacement
        return alias.run()


def conditional_module_selection(flag):
    selected = api if flag else alternative_api
    chained = selected
    return selected.run(), chained.run()


def boolean_module_selection():
    selected = api or alternative_api
    return selected.run()


def linear_module_alias():
    alias = api
    chained = alias
    return chained.run()


def saved_external_member():
    saved = api.run
    return saved(), api.run()


import builtins as native_api
from builtins import len as NativeLength, type as NativeType


def explicit_builtin(values):
    return NativeLength(values)


def qualified_builtin(values):
    return native_api.len(values)


def metadata_only(value: NativeType):
    return value
