def consume(value):
    return value


def read_attribute(obj):
    return consume(obj.value)


def call_unknown_member(obj):
    return obj.consume(consume)


def call_unknown_member_with_keyword(obj):
    return obj.consume(value=consume)
