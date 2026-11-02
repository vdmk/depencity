class Publisher:
    global public_value
    public_value = 1

    with manager:
        del public_value


def keep(cls):
    return cls


@(decorator_alias := keep)
class DeletesDecoratorAlias:
    global decorator_alias
    del decorator_alias


class DeletesKeywordAlias(metaclass=(keyword_alias := type)):
    global keyword_alias
    del keyword_alias
