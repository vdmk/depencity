if flag:
    from .a import work
else:
    from .b import work

from .worker import unused

from .worker import work as mixed


if flag:
    def mixed():
        return local_value
