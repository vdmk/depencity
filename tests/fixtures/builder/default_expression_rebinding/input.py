def positional_and_keyword_only(x, new):
    def child(a=x, b=(x := new), *, c=x):
        return a, b, c

    return child


def lambda_defaults(x, new):
    child = lambda a=x, b=(x := new): (a, b)
    return child


def decorated_default(x, new, decorator):
    @decorator(x)
    def child(value=(x := new)):
        return value

    return child


def class_declaration(x, new, base, meta):
    class Child(base[x], metaclass=(x := new)):
        pass

    return Child


def main(replacement):
    def child(first=value, second=(value := replacement)):
        return first, second

    return child


def unbound_keyword_default(replacement):
    def child(*, first=value, second=(value := replacement)):
        return first, second

    return child


def unbound_decorator(replacement):
    @value
    def child(first=(value := replacement)):
        return first

    return child


def unbound_lambda_defaults(replacement):
    return lambda first=value, second=(value := replacement): (first, second)
