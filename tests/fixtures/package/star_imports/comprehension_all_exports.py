__all__ = ["comprehension_public"]
comprehension_public = 1

items = [__all__ for __all__ in range(2)]
unique = {__all__ for __all__ in range(2)}
mapping = {__all__: __all__ for __all__ in range(2)}
deferred = (__all__ for __all__ in range(2))
local_mutations = [__all__.append("local") for __all__ in [[]]]
nested = [[__all__ for __all__ in range(2)] for item in range(2)]
