from .worker import *
from .dynamic import *
from .attribute_annotations import *
from .subscript_annotations import *
from .dotted_import import *
from .aliased_dotted_import import *
from .declared_exports import *


def main(value):
    return _work(value), hidden(value), attribute_public(value), subscript_public(value)


def import_exports(value):
    return dotted_public(value), _aliased_private(value), aliased_public(value)


def declared_exports(value):
    return _declared_private(value)
