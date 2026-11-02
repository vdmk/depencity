module_value = 0


def duplicate_reads(value):
    return value + value


def attribute_write(obj, value):
    obj.field = value
    return obj.field


def call_value(function, value):
    return function(value)


def closure(value):
    def inner():
        return value

    return inner
