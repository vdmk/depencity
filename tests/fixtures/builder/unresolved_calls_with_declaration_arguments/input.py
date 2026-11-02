seed = 1


def dependency_default(value=seed):
    return value


def constant_default(value=1):
    return value


@decorator
def decorated(value=1):
    return value


def main():
    return (
        external(dependency_default),
        external(constant_default),
        external(decorated),
    )
