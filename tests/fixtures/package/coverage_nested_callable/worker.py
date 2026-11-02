def decorate(function):
    def wrapper():
        return function()

    return wrapper


@decorate
def wrapped():
    return 1
