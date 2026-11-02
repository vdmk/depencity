__all__ = [
    "unused_public",
    "_unused_private",
    "used_public",
    "_used_private",
    "reexported_public",
    "_reexported_private",
    "_AnnotationOnly",
]


def unused_public(value):
    return value


def _unused_private(value):
    return value


def used_public(value):
    return value


def _used_private(value):
    return value


def reexported_public(value):
    return value


def _reexported_private(value):
    return value


class _AnnotationOnly:
    pass
