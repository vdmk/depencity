class C:
    def method(self):
        return 1

    def variadic(*args):
        return args.method()


def main(positional_only: C, /, regular: C, *items: C, keyword_only: C, **named: C):
    positional_only_call = positional_only.method()
    regular_call = regular.method()
    keyword_only_call = keyword_only.method()
    variadic_positional_call = items.method()
    variadic_keyword_call = named.method()
    variadic_method_call = C.variadic()
    return (
        positional_only_call,
        regular_call,
        keyword_only_call,
        variadic_positional_call,
        variadic_keyword_call,
        variadic_method_call,
    )
