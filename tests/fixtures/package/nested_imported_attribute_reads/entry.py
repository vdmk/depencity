import nested_imported_attribute_reads.package as package
import external_package
from .package.worker.config import supply, shared


def main():
    two_components = package.worker.VALUE
    three_components = package.worker.config.VALUE
    reassigned = package.worker.config.REASSIGNED
    missing_module = package.worker.missing.VALUE
    missing_member = package.worker.config.MISSING
    shadowed_intermediate = package.shadowed_worker.config.VALUE
    external = external_package.worker.VALUE
    return (
        two_components,
        three_components,
        reassigned,
        missing_module,
        missing_member,
        shadowed_intermediate,
        external,
    )


def qualified_function_argument(action):
    return action(package.worker.config.supply)


def direct_function_argument(action):
    return action(supply)


def qualified_function_alias():
    saved = package.worker.config.supply
    return saved()


def qualified_class_alias():
    saved = package.worker.config.Product
    return saved().run()


def qualified_method_alias():
    saved = package.worker.config.Product.run
    return saved()


def inherited_method_alias():
    saved = package.worker.config.DerivedProduct.run
    return saved()


def qualified_method_argument(action):
    return action(package.worker.config.Product.run)


def qualified_method_control():
    return package.worker.config.Product.run()


def qualified_instance_receiver():
    qualified = package.worker.config.shared.instance_run()
    direct = shared.instance_run()
    saved = package.worker.config.shared
    aliased = saved.instance_run()
    return qualified, direct, aliased


def qualified_annotated_receiver():
    qualified = package.worker.config.annotated.instance_run()
    saved = package.worker.config.annotated
    return qualified, saved.instance_run()


def replaced_function_value(replacement):
    package.worker.config.supply = replacement
    saved = package.worker.config.supply
    return saved()


def deleted_function_value():
    del package.worker.config.supply
    saved = package.worker.config.supply
    return saved()


def function_saved_before_write(replacement):
    saved = package.worker.config.supply
    package.worker.config.supply = replacement
    return saved()


def sibling_write(replacement):
    package.worker.config.VALUE = replacement
    saved = package.worker.config.supply
    return saved()


def imported_annotated_value():
    from .package.worker.config import annotated, updated

    saved = annotated
    return annotated.instance_run(), saved.instance_run(), updated.instance_run()


def imported_annotation_origin():
    from .package.worker.config import annotated

    Product = unrelated_type
    return annotated.instance_run(), Product


def imported_constructed_value():
    alias = shared
    return shared.instance_run(), alias.instance_run()


def imported_value_alias_chain():
    first = shared
    second = first
    return second.instance_run()
