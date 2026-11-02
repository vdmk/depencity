from module import imported as renamed
import package.module as module_alias


GLOBAL_VALUE = 0


@class_decorator
class Container(Base, metaclass=Meta):
    class_value = 1

    def method(self, value: int = GLOBAL_VALUE):
        return self.class_value + value


def main(seed: int) -> int:
    global GLOBAL_VALUE
    value = seed

    def update(delta: int = seed):
        nonlocal value
        value += delta
        return value

    class Local:
        class_value = seed

        def method(self):
            return self.class_value + value

    GLOBAL_VALUE = update(renamed(value))
    instance = Local()
    return instance.method() + module_alias.adjust(GLOBAL_VALUE)
