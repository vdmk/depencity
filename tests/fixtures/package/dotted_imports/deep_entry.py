import dotted_imports.nested.worker


def main():
    return dotted_imports.nested.worker.f()


def relative_namespace():
    from . import nested

    return nested.worker.f()


def aliased_namespace():
    from . import nested

    alias = nested
    return alias.worker.f()
