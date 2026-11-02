class A:
    def run(self, value):
        return 1


class B:
    def run(self, value):
        return 2


def positional_argument():
    receiver = A()
    return receiver.run(receiver := B())


def keyword_argument():
    receiver = A()
    return receiver.run(value=(receiver := B()))


def main(receiver: A, replacement: B):
    first = receiver.run(receiver := replacement)
    return first, receiver.run(replacement)


def annotated_keyword_argument(receiver: A, replacement: B):
    first = receiver.run(value=(receiver := replacement))
    return first, receiver.run(replacement)
