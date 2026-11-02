__all__: list[str]

ghost: int
initialized: int = 1
existing = 1
existing: str


def annotation_helper(value):
    return value


(attribute_alias := annotation_helper).field: int
_holder = {}
_holder[(subscript_alias := annotation_helper)]: int
