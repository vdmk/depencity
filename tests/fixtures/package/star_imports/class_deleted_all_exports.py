__all__ = ["_formerly_explicit"]
_formerly_explicit = 1
class_deletion_public = 2


class ClearExports:
    global __all__
    del __all__


class RemoveGlobal:
    global removed_by_class
    removed_by_class = 3
    del removed_by_class


class RestoreGlobal:
    global restored_by_class
    restored_by_class = 4
    del restored_by_class
    restored_by_class = 5
