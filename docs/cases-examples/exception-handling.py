def main(value, divisor):
    try:
        result = value / divisor
    except ZeroDivisionError as error:
        result = error
    return result
