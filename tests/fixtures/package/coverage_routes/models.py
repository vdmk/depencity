shared = 0


class Base:
    def __init__(self, value):
        self.value = value


def exported(value):
    return value


class ClassWrites:
    global shared
    try:
        shared = 1
    except Exception as error:
        shared = 2
    except:
        shared = 3
    match {"value": 3}:
        case {"value": captured}:
            shared = captured
