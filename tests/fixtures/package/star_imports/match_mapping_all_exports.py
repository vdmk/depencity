__all__ = ["stale_match_mapping"]
stale_match_mapping = 1
replacement = 2

match {"replacement": 2}:
    case {**__all__}:
        pass
