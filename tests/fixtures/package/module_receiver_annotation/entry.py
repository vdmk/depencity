from . import worker


def invoke(value: worker):
    return value.run()
