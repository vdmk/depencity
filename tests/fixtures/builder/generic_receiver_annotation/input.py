class C:
    def method(self):
        return 1


def main(
    items: list[C],
    typed: C,
    nested: list[list[C]],
    untyped,
    reassigned: list[C],
):
    container_method = items.method()
    element_method = items[0].method()
    nested_element_method = nested[0][0].method()
    untyped_element_method = untyped[0].method()
    reassigned = untyped
    reassigned_element_method = reassigned[0].method()
    return (
        container_method,
        element_method,
        nested_element_method,
        untyped_element_method,
        reassigned_element_method,
        typed.method(),
    )
