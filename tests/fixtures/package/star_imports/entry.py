from external_api import *
from .unknown_export_facade import *
from .chained_all_exports import *
from .empty_all_exports import *
from .escaped_all_exports import *
from .annotation_exports import *
from .defaults import *
from .deletion_exports import *
from .deleted_all_exports import *
from .dynamic import *
from .explicit_deletion_exports import *
from .explicit_annotation_exports import *
from .explicit_patterns import *
from .patterns import *
from .worker import *
from .class_global_exports import *
from .class_deleted_all_exports import *
from .exception_exports import *
from .comprehension_all_exports import *
from .comprehension_all_mutation import *
from .match_as_all_exports import *
from .match_star_all_exports import *
from .match_mapping_all_exports import *


def main(value):
    return (
        transform(value),
        _visible(value),
        public_action(value),
        dynamic_public(value),
        external_transform(value),
        default_alias(value),
        lambda_default_alias(value),
        public_value,
    )


def deferred_alias_consumer(value):
    return deferred_alias(value)


def declaration_expression_aliases():
    return decorator_alias, base_alias


def pattern_rest_values():
    return rest, nested_rest, _explicit_rest


def implicit_private_rest_value():
    return _private_rest


def missing_annotation_export():
    return ghost


def annotation_export_values():
    return initialized, existing, declared_only


def annotation_target_aliases(value):
    return attribute_alias(value), subscript_alias(value)


def deletion_export_values():
    return restored, conditional, _visible


def deleted_implicit_export():
    return removed


def context_export_values():
    return context_value


def deleted_context_export():
    return removed_in_context


def deleted_explicit_export():
    return explicitly_removed


def missing_class_local_export():
    return class_local_value


def class_annotation_target_aliases(value):
    return attribute_global(value), subscript_global(value)


def missing_class_comprehension_exports():
    return list_item, set_item, dict_item, generator_item, nested_item


def exception_alias_exports():
    return prior_alias, rebound_alias, possible_alias


def missing_exception_alias():
    return absent_alias


def class_exception_alias_exports():
    return class_rebound_alias, class_prior_alias


def missing_class_exception_alias():
    return class_absent_alias


def deleted_all_export_values():
    return public_after_all_deletion


def missing_private_after_all_deletion():
    return _private_after_all_deletion


def possible_pattern_exports():
    return stale_match_as, stale_match_star, stale_match_mapping


def comprehension_export_values():
    return comprehension_public


def possible_comprehension_exports():
    return stale_comprehension_export


def class_deletion_exports():
    return class_deletion_public, ClearExports, restored_by_class


def missing_class_deletion_exports():
    return _formerly_explicit, removed_by_class


def possible_alias_exports():
    return stale_alias_export, added_alias_export, stale_chained_export


def empty_export_values():
    return hidden_by_empty_all


def possible_escaped_exports():
    return escaped_first, escaped_second


def exception_header_export():
    return header_alias
