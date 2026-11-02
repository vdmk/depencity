def main(flag):
    if flag:
        from .one import work
    else:
        from .two import work
    return work()


def reversed_order(flag):
    if flag:
        from .two import work
    else:
        from .one import work
    return work()


def same_target(flag):
    if flag:
        from .one import work
    else:
        from .one import work as work
    return work()


def internal_and_external(flag):
    if flag:
        from .one import work
    else:
        from .outside import work
    return work()


def replaced_after_conditional(flag):
    if flag:
        from .one import work
    else:
        from .two import work
    work = replacement
    return work()


def call_conditional_external_member(flag):
    if flag:
        import external_api as api
        return api.run()


def construct_conditional_external_base(flag):
    if flag:
        from external_api import Base

        class Child(Base):
            pass

        return Child()
