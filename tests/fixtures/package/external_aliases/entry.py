from unavailable_graph_library import my_func as f
from unavailable_graph_one import run as same
from .other import helper


def main():
    f()
    same()
    return helper()


from .other import size


def reexported_builtin(items):
    saved = size
    return size(items), saved(items)


from .other import api, saved_api


def reexported_module(value):
    local = saved_api
    return api.run(value), saved_api.run(value), local.run(value)


from . import other


def qualified_reexport(value):
    return other.api.run(value), other.saved_api.run(value)


def nested_qualified_reexport(value):
    return other.api.sub.run(value), other.saved_api.sub.run(value)
