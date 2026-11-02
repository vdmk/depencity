from .worker import A, B, Holder

saved_member = Holder.value
member_result = saved_member.method()


def main():
    value = A()
    first = value.method()
    value = B()
    return value.method()


def replace_member(value: A, replacement):
    value.method = replacement
    return value.method()


def delete_member(value: A):
    del value.method
    return value.method()


def call_before_write(value: A, replacement):
    before = value.method()
    value.method = replacement
    return before, value.method()


def rebind_after_write(value: A, replacement):
    value.method = replacement
    value = B()
    return value.method()


def write_other_member(value: A, replacement):
    value.other = replacement
    return value.method()
