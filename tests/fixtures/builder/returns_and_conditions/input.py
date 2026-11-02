def main(flag: bool, value: int) -> int:
    if flag:
        return 1
    if value < 0:
        return -1
    return value


def early_if(flag, value):
    if flag:
        return value
    else:
        result = value
    after = value
    return after


def early_else(flag, value):
    if flag:
        result = value
    else:
        return value
    after = value
    return after


def nested_early(outer, inner, value):
    if outer:
        if inner:
            return value
        inside = value
    after = value
    return after


def consecutive_guards(first, second, value):
    if first:
        return value
    if second:
        return value
    return value


def elif_guards(first, second, value):
    if first:
        return value
    elif second:
        return value
    return value


def no_terminating_branch(flag, value):
    if flag:
        result = value
    else:
        result = value
    after = value
    return after


def final_replacement(flag, old, replacement):
    try:
        if flag:
            return old
    finally:
        return replacement


def guarded_final_replacement(outer, flag, old, replacement):
    if outer:
        try:
            if flag:
                return old
        finally:
            return replacement


def recover_before_branch(action, flag, old, recovery):
    try:
        action()
        if flag:
            return old
    except Exception:
        return recovery


def suppressed_body_exit(manager, action, flag, old, replacement):
    with manager:
        action()
        if flag:
            return old
    return replacement


async def suppressed_async_body_exit(manager, action, flag, old, replacement):
    async with manager:
        action()
        if flag:
            return old
    return replacement


def trailing_pass_after_return(flag, early, late):
    if flag:
        return early
        pass
    return late()


def trailing_pass_after_raise(flag, failure, late):
    if flag:
        raise failure
        pass
    return late()


def trailing_pass_after_branches(outer, inner, left, right, late):
    if outer:
        if inner:
            return left
        else:
            return right
        pass
    return late()


def safe_with_branch(flag, manager, late):
    if flag:
        with manager:
            return 1
    return late()


def suppressible_with_branch(flag, manager, action, late):
    if flag:
        with manager:
            return action()
    return late()


def handled_return_branch(flag, action, recovery, late):
    if flag:
        try:
            return action()
        except Exception:
            return recovery
    return late()


def finally_after_guard(flag, early, cleanup, late):
    try:
        if flag:
            return early
    finally:
        cleanup()
    return late()


def finally_after_raise(flag, failure, cleanup, late):
    try:
        if flag:
            raise failure
    finally:
        cleanup()
    return late()


def body_and_final_guards(flag, stop, early, replacement, cleanup, late):
    try:
        if flag:
            return early
    finally:
        cleanup()
        if stop:
            return replacement
    return late()


def ordinary_finally_body(flag, cleanup, late):
    try:
        if flag:
            pass
    finally:
        cleanup()
    return late()


def recovered_exit_guard(flag, action, early, cleanup, late):
    try:
        action()
        if flag:
            return early
    except Exception:
        pass
    finally:
        cleanup()
    return late()


def consecutive_returns(first, second):
    return first
    return second


def returning_branch(flag, first, second):
    if flag:
        return first
        return second
    return first


def raising_body(failure, value):
    raise failure
    return value


def suppressible_return(manager, first, second):
    with manager:
        return first
    return second


def return_candidates(flag, first, second, failure, manager):
    return (
        consecutive_returns(first, second),
        returning_branch(flag, first, second),
        raising_body(failure, second),
        suppressible_return(manager, first, second),
        returning_try_else(first, second),
        guarded_try_else(flag, first, second),
        suppressible_try_else(manager, first, second),
    )


def returning_try_else(value, other):
    try:
        return value
    except Exception:
        raise
    else:
        return other


def guarded_try_else(flag, value, other):
    try:
        if flag:
            return value
    except Exception:
        raise
    else:
        return other


def suppressible_try_else(manager, value, other):
    try:
        with manager:
            return value
    except Exception:
        raise
    else:
        return other
