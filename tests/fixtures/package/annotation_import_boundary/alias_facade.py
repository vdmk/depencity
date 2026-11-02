from .worker import Worker

Alias = Worker
AliasChain = Alias


class Namespace:
    Alias = Worker


__all__ = ["Alias"]
