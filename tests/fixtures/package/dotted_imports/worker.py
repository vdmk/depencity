def f():
    return 'worker'


class Factory:
    def run(self):
        return direct_payload


class worker:
    class Factory:
        def run(self):
            return nested_payload
