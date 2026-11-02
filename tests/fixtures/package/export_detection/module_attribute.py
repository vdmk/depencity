import typing as types

value = types.Any


def conditional_shadow(condition):
    if condition:
        types = object()
    return types.Any
