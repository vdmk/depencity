__all__ = ['public_value']

match {'value': 1}:
    case {'value': captured}:
        pass


def public_value():
    return captured
