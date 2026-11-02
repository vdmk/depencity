source = external_source
VALUE = source

alias_source = external_alias_source
VALUE_ALIAS = alias_source

REASSIGNED = original_value
REASSIGNED = current_value

DELETED = deleted_value
del DELETED

CONDITIONAL = conditional_value
if should_delete:
    del CONDITIONAL

REBOUND = deleted_value
del REBOUND
REBOUND = restored_value
