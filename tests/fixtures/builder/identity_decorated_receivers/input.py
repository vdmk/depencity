def identity(function):
    return function


def replacement(function):
    return alternate


def alternate(self):
    return self.run()


class Worker:
    def run(self):
        return original

    def plain(self):
        return self.run()

    @identity
    def decorated(self):
        return self.run()

    @identity
    @identity
    def stacked(self):
        return self.run()

    @identity
    @staticmethod
    def static(self):
        return self.run()

    @identity
    @classmethod
    def class_method(cls):
        return cls.run()

    @opaque
    def unknown(self):
        return self.run()

    @replacement
    def replaced(self):
        return self.run()


def main():
    worker = Worker()
    return worker.plain(), worker.decorated(), worker.stacked()


def installed_method(receiver):
    return receiver.run()


class Installed:
    method = installed_method

    def run(self):
        return installed_payload


def installed_call():
    return Installed().method()


class ReplacedQualifiedStaticmethod:
    import builtins as decorators

    decorators.staticmethod = identity

    def action(self):
        return payload

    @decorators.staticmethod
    def run(self):
        return self.action()
