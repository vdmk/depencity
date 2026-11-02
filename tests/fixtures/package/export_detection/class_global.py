__all__ = ["export"]


class ReplaceExports:
    global __all__
    __all__ = ["export"]


class CaptureExports:
    global __all__
    match "export":
        case __all__:
            pass


class CaptureUnpackedExports:
    global __all__
    match ["export"]:
        case [*__all__]:
            pass
    match {"export": "export"}:
        case {**__all__}:
            pass


class CatchExports:
    global __all__
    try:
        raise RuntimeError
    except RuntimeError as __all__:
        pass


class ImportExports:
    global __all__
    import typing as __all__


class FromImportExports:
    global __all__
    from typing import Any as __all__


class LambdaExports:
    global __all__
    __all__ = lambda value=export: value
    marker: str = "marker"
    annotation_only: str


def export(value):
    return value
