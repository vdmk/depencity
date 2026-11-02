try:
    from .facade import *
except ImportError:
    from .fallback import *

if external_enabled:
    from external_api import *


def main():
    return run(), external_function()


def private_from_facade():
    return _work()
