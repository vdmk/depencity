class Worker:
    @staticmethod
    def run():
        return first

    @classmethod
    def build(cls):
        return cls


class OtherWorker:
    @staticmethod
    def run():
        return second


class Outer:
    Alias = Worker


class Inherited(Outer):
    pass


class Conditional:
    Alias = Worker
    if enabled:
        Alias = OtherWorker


class Rebound:
    Alias = Worker
    Alias = unknown


def main():
    saved = Outer.Alias.run
    inherited = Inherited.Alias.run
    conditional = Conditional.Alias.run
    bound = Outer.Alias.build
    return saved(), inherited(), conditional(), Outer.Alias.run(), bound()


def unknown_rebinding():
    saved = Rebound.Alias.run
    return saved()


def replaced_intermediate(replacement):
    Outer.Alias = replacement
    saved = Outer.Alias.run
    return saved()
