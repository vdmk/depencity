def unmatched_cases(subject, old):
    value = old
    match subject:
        case 1:
            value = first
        case 2:
            value = second
    return value


def guarded_wildcard_cases(subject, enabled, old):
    value = old
    match subject:
        case 1 if enabled:
            value = first
        case 2:
            value = second
        case _:
            value = fallback
    return value


def guard_rebinds_subject(x, new):
    match x:
        case 1 if (x := new):
            return x
        case 2:
            return x


def body_rebinds_subject(x, new):
    match x:
        case 1:
            x = new
        case 2:
            return x


def qualified_patterns(subject, namespace):
    match subject:
        case namespace.FIRST:
            return first
        case namespace.SECOND:
            return second
        case namespace.Kind():
            return third


class Worker:
    def run(self):
        return payload


def captured_receiver(subject):
    match subject:
        case Worker() as value:
            return value.run()


def annotated_subject(subject: Worker):
    match subject:
        case Worker():
            return subject.run()


def returning_case(subject, early, late):
    match subject:
        case 1:
            return early
    return late()


def raising_case(subject, failure, late):
    match subject:
        case 1:
            raise failure
    return late()


def guarded_returning_case(subject, enabled, early, late):
    match subject:
        case 1 if enabled:
            return early
    return late()


def conditional_case_return(subject, enabled, early, late):
    match subject:
        case 1:
            if enabled:
                return early
        case 2:
            pass
    return late()


def nested_returning_case(subject, inner, early, late):
    match subject:
        case 1:
            match inner:
                case 2:
                    return early
    return late()


def ordinary_case_body(subject, action, late):
    match subject:
        case 1:
            action()
    return late()


def suppressible_case_return(subject, manager, action, late):
    match subject:
        case 1:
            with manager:
                return action()
    return late()


def action():
    return payload


def replaced_capture(subject):
    callback = action
    match subject:
        case callback if callback:
            callback()
    return callback


def guarded_capture(enabled, subject):
    callback = action
    if enabled:
        match subject:
            case callback:
                callback()
    return callback


def typed_capture(subject, value: Worker):
    match subject:
        case [value]:
            return value.run()


def alternate_action():
    return replacement_payload


def later_case_reads(subject):
    callback = action
    match subject:
        case 1:
            callback = alternate_action
        case 2 if callback():
            callback()
    return callback
