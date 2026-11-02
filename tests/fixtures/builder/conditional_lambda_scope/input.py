def main(flag, captured, default):
    if flag:
        lambda_function = lambda value=default: value + captured

        def regular_function(value=default):
            return value + captured

    return lambda_function, regular_function
