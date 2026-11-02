global_value = 1


def local_name(value, replacement):
    value += (value := replacement)
    return value


def global_name(replacement):
    global global_value
    global_value += (global_value := replacement)
    return global_value


def nonlocal_name(replacement):
    value = 1

    def update():
        nonlocal value
        value += (value := replacement)
        return value

    return update()


def attribute_target(obj, replacement):
    obj.value += (obj := replacement)
    return obj


def subscript_target(items, index, replacement_index):
    items[index] += (index := replacement_index)
    return items


def subscript_object_target(items, index, replacement_items):
    items[index] += (items := replacement_items)
    return items


def subscript_index_rebind(items, index):
    items[(items := index)] = 1
    return items


def augmented_subscript_index_rebind(items, index, value):
    items[(items := index)] += value
    return items


def attribute_control(obj, value):
    obj.value += value


def side_effecting_target(value):
    get_object().items[get_index()] += value


def call_receiver(replacement):
    get_object().value += (value := replacement)
    return value


def main(replacement):
    value += (value := replacement)
    return value


def shadow_outer_name(replacement):
    global_value += (global_value := replacement)
    return global_value


def shadow_builtin_name(replacement):
    len += (len := replacement)
    return len


class Counter:
    def update(self, replacement):
        self.value += (self := replacement)

    def update_nested(self, replacement):
        self.inner.value += (self := replacement)

    @classmethod
    def update_class(cls, replacement):
        cls.value += (cls := replacement)

    def assign_after_rebinding(self, replacement):
        self.value = (self := replacement)


def sibling_augmented(flag, old, new, delta):
    value = old
    if flag:
        value = new
    else:
        value += delta
    return value
