from .unused_star_exports import *


def use(value: _AnnotationOnly):
    return used_public(value), _used_private(value)
