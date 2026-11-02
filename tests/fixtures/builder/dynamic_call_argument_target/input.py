def helper():
    return 1


def keyword_helper():
    return 2


def main():
    return factory()(helper, callback=keyword_helper)


def known_dynamic():
    return (lambda: 3)()
