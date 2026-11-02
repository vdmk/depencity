class Worker:
    def normalize(self, value):
        return value

    def run(self, value):
        return self.normalize(value)

    def renamed_receiver(receiver, value):
        return receiver.normalize(value)

    @staticmethod
    def static(self, value):
        return self.normalize(value)

    def with_nested_function(self):
        def nested(self, value):
            return self.normalize(value)

        return nested


class Child(Worker):
    def run_inherited(self, value):
        return self.normalize(value)


def main(worker: Worker, child: Child, value):
    return (
        worker.run(value),
        worker.renamed_receiver(value),
        child.run_inherited(value),
        Worker.static(worker, value),
    )
