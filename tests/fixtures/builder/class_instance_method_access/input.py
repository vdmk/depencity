class Parent:
    @staticmethod
    def inherited_static():
        return 0

    @classmethod
    def inherited_class(cls):
        return cls.inherited_static()

    def inherited_ordinary(self):
        return 3


class C(Parent):
    value = source

    @staticmethod
    def static_method():
        return 1

    @classmethod
    def class_method(cls):
        return cls.static_method()

    def ordinary_method(self):
        return 2


def main(instance: C):
    class_static = C.static_method
    instance_static = instance.static_method
    class_class = C.class_method
    instance_class = instance.class_method
    class_ordinary = C.ordinary_method
    instance_ordinary = instance.ordinary_method
    class_inherited_class = C.inherited_class
    instance_inherited_class = instance.inherited_class
    class_inherited_ordinary = C.inherited_ordinary
    instance_inherited_ordinary = instance.inherited_ordinary
    class_value = C.value
    instance_value = instance.value
    return (
        class_static,
        instance_static,
        class_class,
        instance_class,
        class_ordinary,
        instance_ordinary,
        class_inherited_class,
        instance_inherited_class,
        class_inherited_ordinary,
        instance_inherited_ordinary,
        class_value,
        instance_value,
        class_static(),
        instance_static(),
        class_class(),
        instance_class(),
        class_ordinary(instance),
        instance_ordinary(),
        class_inherited_class(),
        instance_inherited_class(),
        class_inherited_ordinary(instance),
        instance_inherited_ordinary(),
        C.static_method(),
        instance.static_method(),
        C.class_method(),
        instance.class_method(),
        C.ordinary_method(instance),
        instance.ordinary_method(),
        C.inherited_class(),
        instance.inherited_class(),
        C.inherited_ordinary(instance),
        instance.inherited_ordinary(),
    )
