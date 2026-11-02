from .worker import Choice, RepeatedChoice, A, B


def main():
    action = Choice
    return action()


def methods(flag):
    receiver = A() if flag else B()
    return receiver.run()


def repeated():
    action = RepeatedChoice
    return action()
