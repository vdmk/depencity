class Worker:
    class_value = source
    class_cell_is_not_in_class_body = __class__

    def class_object(self):
        return __class__

    def nested_reader(self):
        def read_class_cell():
            return __class__

        return read_class_cell()

    def enclosing_class_cell_shadow(self):
        __class__ = replacement

        def read_shadowed_class_cell():
            return __class__

        return read_shadowed_class_cell()

    def class_namespace_is_not_a_closure(self):
        return class_value


def unrelated():
    def read_class_cell():
        return __class__, Worker

    return read_class_cell()


def main():
    return Worker.class_object()
