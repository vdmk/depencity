class Worker:
    VALUE = 3

    def run(self):
        return self.VALUE


def conditional_value(value: Worker, flag):
    first = value.VALUE
    if flag:
        second = value.VALUE
        return second
    return first


def guarded_saved_method(value: Worker, flag):
    if flag:
        saved = value.run
        return saved
    return None


def loop_member_value(value: Worker, items):
    result = None
    for item in items:
        result = value.VALUE
    return result


def comprehension_filter(value: Worker, items):
    return [item for item in items if value.VALUE]


def direct_method(value: Worker):
    return value.run()


def overwritten_method(value: Worker, callback):
    value.run = callback
    return value.run()


def saved_overwritten_method(value: Worker, callback):
    value.run = callback
    saved = value.run
    return saved()


def saved_deleted_method(value: Worker):
    del value.run
    saved = value.run
    return saved()


def constructed_overwrite(callback):
    value = Worker()
    value.run = callback
    return value.run()


def class_overwrite(callback):
    Worker.run = callback
    return Worker.run()


def conditional_overwrite(value: Worker, callback, flag):
    if flag:
        value.run = callback
    return value.run()


def deleted_method(value: Worker):
    del value.run
    return value.run()


def unrelated_overwrite(value: Worker, callback):
    value.VALUE = callback
    return value.run()


def rebound_receiver(value: Worker, replacement: Worker, callback):
    value.run = callback
    value = replacement
    return value.run()


class OtherWorker:
    def run(self):
        return 2


def save_selected_method(flag):
    saved = (Worker() if flag else OtherWorker()).run
    return saved()


def save_constructed_method():
    saved = Worker().run
    return saved()


def save_annotated_method(flag, left: Worker, right: OtherWorker):
    saved = (left if flag else right).run
    return saved()


def ignore_condition_receiver(flag: Worker, unknown):
    saved = (unknown if flag else unknown).run
    return saved()


def ignore_arithmetic_receiver(left: Worker, right: OtherWorker):
    saved = (left + right).run
    return saved()
