__all__ = ['public_value']
first = [1]
second = [2]
combined = [left for left in first for right in second if __all__]


def public_value():
    return combined
