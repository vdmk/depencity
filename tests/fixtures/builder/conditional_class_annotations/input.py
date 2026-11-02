class Original:
    def run(self):
        return original_payload


class Updated:
    def run(self):
        return updated_payload


class Ordinary:
    item: Original = unknown
    item: Updated


if enabled:
    class Guarded:
        item: Original = unknown
        item: Updated

    class Conditional:
        item: Original = unknown
        if selected:
            item: Updated

    class Outer:
        class Nested:
            item: Original = unknown
            item: Updated


def main():
    return Ordinary.item.run(), Guarded.item.run(), Conditional.item.run(), Outer.Nested.item.run()
