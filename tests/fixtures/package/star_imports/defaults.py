def public_action(value):
    return value


def identity_decorator(function):
    return function


@ (decorator_alias := identity_decorator)
def decorated():
    return 1


def default_holder(value=(default_alias := public_action)):
    return value


lambda_holder = lambda value=(lambda_default_alias := public_action): value


class Parent:
    pass


class Child((base_alias := Parent)):
    pass


def deferred_bindings():
    deferred_alias = public_action
    return lambda: (deferred_lambda_alias := public_action)


def _private_action(value):
    return value
