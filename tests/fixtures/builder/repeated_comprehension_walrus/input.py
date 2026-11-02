def main(items):
    return [(value := item) for item in items if (value := item)]


global_value = 0


def global_writes(items):
    global global_value
    return [
        (global_value := item)
        for item in items
        if (global_value := item)
    ]


def nonlocal_writes(items):
    value = 0

    def update():
        nonlocal value
        return [
            (value := item)
            for item in items
            if (value := item)
        ]

    return update()
