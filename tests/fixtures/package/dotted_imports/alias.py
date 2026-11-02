import dotted_imports.worker as worker


def main():
    return worker.f()


def same_root_alias():
    import dotted_imports.worker as dotted_imports
    return dotted_imports.worker.Factory().run()
