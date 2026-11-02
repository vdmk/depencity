from . import worker


def main():
    receiver = worker.A()
    return receiver.run(receiver := worker.B())


def keyword_argument():
    receiver = worker.A()
    return receiver.run(value=(receiver := worker.B()))


def unbound_receiver():
    return receiver.run(receiver := worker.B())


def reverse_rebinding():
    receiver = worker.B()
    return receiver.run(receiver := worker.A())
