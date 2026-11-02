def run(value=None):
    return payload


Alias = run


class A:
    def run(self, value=None):
        return member_payload


from .worker import Alias as SelfAlias


def same_source():
    return SelfAlias(run)


@decorate
def configured(value=default_value):
    return configured_payload


class Derived(base_value):
    pass
