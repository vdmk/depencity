class Known:
    def run(self):
        return annotated_payload


class A:
    def run(self):
        return payload

    def method(self, callback=lambda obj: obj.run()):
        return callback

    callbacks = [lambda obj: obj.run()]
    registered = register(lambda obj: obj.run())
    direct = lambda self: self.run()

    if enabled:
        conditional = lambda receiver: receiver.run()

    @staticmethod
    def static(obj):
        return obj.run()

    @staticmethod
    def annotated(obj: Known):
        return obj.run()

    @classmethod
    def class_method(cls):
        return cls.make()

    @staticmethod
    def make():
        return class_payload

    global escaped

    def escaped(obj):
        return obj.run()


def module_default(callback=lambda obj: obj.run()):
    return callback


def main(value: A):
    return value.direct(), value.conditional(), A.annotated(value), A.class_method()
