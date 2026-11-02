class Known:
    def run(self):
        return payload


def unpacked_tuple[*Ts](values: tuple[*Ts]):
    return values[0].run()


def mixed_unpacked_tuple[*Ts](values: tuple[Known, *Ts]):
    return values[0].run()


def unpacked_list[*Ts](values: list[*Ts]):
    return values[0].run()


def sliced_annotation(values: list[Known:Known]):
    return values[0].run()


def ordinary_tuple(values: tuple[Known, ...]):
    return values[0].run()
