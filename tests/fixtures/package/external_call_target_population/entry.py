from .worker import generated
from .worker import helper
from .worker import multiple
from unavailable_graph import shared as external_alias
from unavailable_graph import shared as second_external_alias


def one_output(flag):
    return helper(flag)


def multiple_outputs(flag):
    return multiple(flag)


def repeated_call(flag):
    helper(flag)
    return helper(flag)


def alias_calls(flag):
    external_alias(flag)
    return second_external_alias(flag)


def generator_outputs(flag):
    return generated(flag)


def main(flag):
    return (
        one_output(flag),
        multiple_outputs(flag),
        repeated_call(flag),
        alias_calls(flag),
        generator_outputs(flag),
    )
