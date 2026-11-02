def first():
    return first_payload


def second():
    return second_payload


Choice = first if flag else second


class A:
    def run(self):
        return a_payload


class B:
    def run(self):
        return b_payload


class Repeated:
    @staticmethod
    def run():
        return earlier_payload

    earlier = run

    @staticmethod
    def run():
        return later_payload

    later = run


RepeatedChoice = Repeated.earlier if flag else Repeated.later
