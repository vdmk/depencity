from .method import A
from .parameter import A as ParameterReader


def main(value):
    obj = A()
    reader = ParameterReader()
    return obj.__run(), obj._A__run(), reader.run(value)
