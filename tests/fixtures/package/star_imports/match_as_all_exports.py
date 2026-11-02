__all__ = ["stale_match_as"]
stale_match_as = 1
replacement = 2

match [["replacement"]]:
    case [__all__]:
        pass
