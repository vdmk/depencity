class Worker:
    def run(self):
        return 1


class Other:
    def run(self):
        return 2


def main(argument, replacement):
    value = argument
    value: Worker
    annotated_call = value.run()
    value = replacement
    rebound_call = value.run()
    return annotated_call, rebound_call


def ordered(value: Worker):
    before = value.run()
    value: Other
    after = value.run()
    return before, after


def uninitialized_local():
    value: Worker
    return value.run()


class Factory:
    @classmethod
    def run(cls):
        return 3


class OtherFactory:
    @classmethod
    def run(cls):
        return 4


def class_object(value, replacement):
    unknown = value.run()
    value: type[Factory]
    first = value.run()
    saved = value
    value: type[OtherFactory]
    second = value.run()
    original = saved.run()
    constructed = value()
    value = replacement
    rebound = value.run()
    return unknown, first, second, original, constructed, rebound


def annotated_class_object(value: type[Factory]):
    first = value.run()
    value: type[OtherFactory]
    second = value.run()
    return first, second


def walrus_class_object(value: type[Factory], replacement: type[OtherFactory]):
    identity(saved := value)
    value: type[OtherFactory]
    value = replacement
    return saved.run()


def deferred_receiver_metadata(value: Worker):
    def read():
        return value.run()

    callback = lambda: value.run()
    pending = (value.run() for item in [0])
    eager = [value.run() for item in [0]]
    value: Other
    return read(), callback(), pending, eager


def eager_class_metadata(value: Worker):
    class Capture:
        result = value.run()

    value: Other
    return Capture.result


def conditional_deferred_metadata(value: Worker, flag):
    def read():
        return value.run()

    if flag:
        value: Other
    return read()
