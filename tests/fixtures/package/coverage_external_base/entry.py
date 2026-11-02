from .worker import Worker as ImportedWorker


def main(value):
    return ImportedWorker(value)
