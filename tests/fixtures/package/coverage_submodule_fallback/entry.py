from .parent import child as child_module


def main(value):
    return child_module.run(value)
