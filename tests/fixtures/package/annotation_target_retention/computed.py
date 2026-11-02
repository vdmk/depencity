from .facade import Factory, Position, Index

Factory().field: int
Factory()[Position()]: int
Factory()[Position():Position()]: int
Factory()[Index]: int
