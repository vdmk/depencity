class Field:
    def __get__(self, instance, owner):
        return instance._value

    def __set__(self, instance, value):
        instance._value = value


class Record:
    value = Field()

    def __init__(self, value):
        self.value = value

    def read(self):
        return self.value
