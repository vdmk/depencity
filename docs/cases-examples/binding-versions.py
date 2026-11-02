shared = 0


def main(value):
    global shared
    total = value
    total = total + 1
    shared = total
    return total
