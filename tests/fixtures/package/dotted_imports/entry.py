import dotted_imports.worker


def main():
    return dotted_imports.worker.f()


def root_alias():
    alias = dotted_imports
    return alias.worker.Factory().run()
