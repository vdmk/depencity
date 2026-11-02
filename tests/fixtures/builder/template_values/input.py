def source():
    return payload


class Known:
    def run(self):
        return member_payload


def main():
    alias = t"{source}"
    return alias()


def direct_alias():
    alias = source
    return alias()


def formatted_string():
    alias = f"{source}"
    return alias()


def class_template():
    alias = t"{Known}"
    value = alias()
    return value.run()


def class_alias():
    alias = Known
    value = alias()
    return value.run()


def empty_template():
    alias = t""
    return alias()


def multiple_interpolations():
    alias = t"{source}:{Known}:{source}"
    return alias()


def format_specification(width):
    alias = t"{source!r:{width}}"
    return alias()
