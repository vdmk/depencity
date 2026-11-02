from .models import Base as ImportedBase, exported
from . import worker


class Child(ImportedBase):
    def __init__(self, value):
        self.value = value


async def main(value):
    await worker.run(value)
    child = Child(value)
    direct = ImportedBase(value)
    return exported((child, direct))


def nested_class_name():
    class Local:
        worker = object()

    return worker.run()
