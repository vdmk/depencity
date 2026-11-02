from .facade import transform
from .dynamic import transform as dynamic_transform


def main(value):
    return transform(value), dynamic_transform(value)
