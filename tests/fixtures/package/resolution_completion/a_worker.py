def action():
    return function_payload


class Worker:
    def __init__(self):
        self.value = instance_payload

    def run(self):
        return self.value

    @staticmethod
    def action():
        return static_payload
