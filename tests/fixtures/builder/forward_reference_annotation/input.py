class Worker:
    def run(self):
        return result


class namespace:
    class Worker:
        def run(self):
            return nested_result


def main(
    value: "Worker",
    qualified: "namespace.Worker",
    expression: "Worker | Other",
    call: "make_type()",
    malformed: "Worker[",
):
    return (
        value.run(),
        qualified.run(),
        expression.run(),
        call.run(),
        malformed.run(),
    )
