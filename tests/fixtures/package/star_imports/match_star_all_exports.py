__all__ = ["stale_match_star"]
stale_match_star = 1
replacement = 2

match ["replacement"]:
    case [*__all__]:
        pass
