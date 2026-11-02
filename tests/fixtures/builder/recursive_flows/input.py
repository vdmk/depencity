def main(values):
    def flatten_list(value):
        if isinstance(value, list):
            return [item for child in value for item in flatten_list(child)]
        return [value]

    def flatten_generator(value):
        if isinstance(value, list):
            for child in value:
                yield from flatten_generator(child)
        else:
            yield value

    return flatten_list(values), list(flatten_generator(values))
