from missing import unused
from missing import work
from .worker import work, extra as alias_extra


worker_result = work()


def first():
    return work()


from .other import work


def second():
    return work()


def alias():
    return alias_extra()


def nested():
    from missing import local_unused
    from .worker import work as local_work

    def child():
        return local_work()

    return child


from . import worker as provider


class CapturedProvider:
    action = provider.work


from . import other as provider
latest_action = provider.work
