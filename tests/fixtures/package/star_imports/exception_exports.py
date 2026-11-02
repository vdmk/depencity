try:
    raise RuntimeError
except RuntimeError as absent_alias:
    pass

prior_alias = 1
try:
    raise RuntimeError
except RuntimeError as prior_alias:
    pass

try:
    raise RuntimeError
except RuntimeError as rebound_alias:
    pass
rebound_alias = 2

possible_alias = 1
try:
    operation()
except Exception as possible_alias:
    possible_alias = replacement


class ClearGlobalAlias:
    global class_absent_alias
    try:
        operation()
    except Exception as class_absent_alias:
        class_absent_alias = replacement


class RebindGlobalAlias:
    global class_rebound_alias
    try:
        operation()
    except Exception as class_rebound_alias:
        pass
    class_rebound_alias = 2


class_prior_alias = 1


class PriorGlobalAlias:
    global class_prior_alias
    try:
        operation()
    except Exception as class_prior_alias:
        pass


def read_class_aliases():
    return class_absent_alias, class_rebound_alias, class_prior_alias


try:
    risky()
except (header_alias := RuntimeError) as header_alias:
    pass
except Exception:
    pass
