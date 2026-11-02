from .worker import run
import shadowed_imports.demo.worker as worker


def main(run):
    return run()


def attribute_main(worker):
    return worker.run()
