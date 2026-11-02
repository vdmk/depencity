from .conditional import *

conditional_result = value

from .direct import *

direct_result = value

from .nested import *

nested_result = value

from .guarded import *

guarded_results = branch_value, loop_value, try_value, with_value, class_with_value


def main():
    return conditional_result, direct_result, nested_result, guarded_results
