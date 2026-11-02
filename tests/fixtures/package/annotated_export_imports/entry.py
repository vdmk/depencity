from external import Public

__all__ = ["Public", "main"]
value: Public


def main(value):
    from local_annotation_only import Public

    value: Public
    return value
