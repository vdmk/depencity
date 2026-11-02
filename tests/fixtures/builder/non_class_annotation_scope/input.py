def factory():
    return None


def consume(value: factory):
    return value.run()


class Worker:
    def run(self):
        return 1


instance = Worker()
instance_alias = instance
class_alias = Worker


def main(
    value: instance,
    alias: instance_alias,
    legitimate: class_alias,
    constructor: type[instance],
):
    return value.run(), alias.run(), legitimate.run(), constructor()
