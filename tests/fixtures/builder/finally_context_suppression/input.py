def suppressed_subscript(first, values, context):
    try:
        return first
    finally:
        with context:
            return values[0]


def suppressed_division(first, zero, context):
    try:
        return first
    finally:
        with context:
            return 1 / zero


def suppressed_raise(first, context):
    try:
        return first
    finally:
        with context:
            raise ValueError


def suppressed_return_call(first, context, risky):
    try:
        return first
    finally:
        with context:
            return risky()


def suppressed_nested_setup(first, replacement, context, risky):
    try:
        return first
    finally:
        with context:
            with risky():
                return replacement


def suppressed_unpacking(first, values, context, replacement):
    try:
        return first
    finally:
        with context:
            left, right = values
            return replacement


def suppressed_list_unpacking(first, values, context, replacement):
    try:
        return first
    finally:
        with context:
            [left, right] = values
            return replacement


def suppressed_truth_test(first, flag, context, replacement):
    try:
        return first
    finally:
        with context:
            if flag:
                return replacement
            else:
                return replacement


def suppressed_truth_test_before_return(first, flag, context, replacement):
    try:
        return first
    finally:
        with context:
            if flag:
                pass
            return replacement


def suppressed_augmented_division(first, replacement, zero, context):
    try:
        return first
    finally:
        with context:
            replacement /= zero
            return replacement


def suppressed_deleted_return(first, replacement, context):
    try:
        return first
    finally:
        with context:
            del replacement
            return replacement


def suppressed_repeated_deletion(first, replacement, context):
    try:
        return first
    finally:
        with context:
            del replacement
            del replacement
            return 0


def suppressed_context_unpacking(first, replacement, context):
    try:
        return first
    finally:
        with context as (left, right):
            return replacement


def suppressed_context_attribute(first, replacement, context, target):
    try:
        return first
    finally:
        with context as target.value:
            return replacement


def suppressed_second_context(first, replacement, context, risky):
    try:
        return first
    finally:
        with context, risky():
            return replacement


async def suppressed_async_context_unpacking(first, replacement, context):
    try:
        return first
    finally:
        async with context as (left, right):
            return replacement


async def suppressed_second_async_context(first, replacement, context, risky):
    try:
        return first
    finally:
        async with context, risky():
            return replacement


def suppressed_missing_global(first, context):
    try:
        return first
    finally:
        with context:
            return missing


def suppressed_unbound_local(first, context, flag):
    if flag:
        replacement = 1
    try:
        return first
    finally:
        with context:
            return replacement


def suppressed_name_read_before_return(first, context):
    try:
        return first
    finally:
        with context:
            value = missing
            return 0


async def suppressed_async_missing_global(first, context):
    try:
        return first
    finally:
        async with context:
            return missing


def constant_context_return(first, context):
    try:
        return first
    finally:
        with context:
            return 0


def constant_context_if_returns(context):
    with context:
        if True:
            return 1
        else:
            return 2


def constant_context_if_without_else(context):
    with context:
        if True:
            return 1
        return 2


def main(first, values, zero, context, replacement, risky, flag, target):
    return (
        suppressed_subscript(first, values, context),
        suppressed_division(first, zero, context),
        suppressed_raise(first, context),
        suppressed_return_call(first, context, risky),
        suppressed_nested_setup(first, replacement, context, risky),
        suppressed_unpacking(first, values, context, replacement),
        suppressed_list_unpacking(first, values, context, replacement),
        suppressed_truth_test(first, flag, context, replacement),
        suppressed_truth_test_before_return(first, flag, context, replacement),
        suppressed_augmented_division(first, replacement, zero, context),
        suppressed_deleted_return(first, replacement, context),
        suppressed_repeated_deletion(first, replacement, context),
        suppressed_context_unpacking(first, replacement, context),
        suppressed_context_attribute(first, replacement, context, target),
        suppressed_second_context(first, replacement, context, risky),
        suppressed_async_context_unpacking(first, replacement, context),
        suppressed_second_async_context(first, replacement, context, risky),
        suppressed_missing_global(first, context),
        suppressed_unbound_local(first, context, flag),
        suppressed_name_read_before_return(first, context),
        suppressed_async_missing_global(first, context),
        constant_context_return(first, context),
        class_definition(context, first),
        decorated_definition(context, first),
        decorated_async_definition(context, first),
        plain_definition(context, first),
    )


def class_definition(manager, value):
    try:
        return value
    finally:
        with manager:
            class Broken(metaclass=None):
                pass
            return 1


def decorated_definition(manager, value):
    try:
        return value
    finally:
        with manager:
            @None
            def inner():
                pass
            return 1


def decorated_async_definition(manager, value):
    try:
        return value
    finally:
        with manager:
            @None
            async def inner():
                pass
            return 1


def plain_definition(manager, value):
    try:
        return value
    finally:
        with manager:
            def inner():
                pass
            return 1
