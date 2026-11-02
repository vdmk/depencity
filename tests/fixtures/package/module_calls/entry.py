import module_calls.worker as worker
import module_calls.alternate as alternate
import external.worker as external_worker


def main(value):
    return worker.transform(value)


def aliased_module():
    alias = worker
    return alias.transform(1)


def module_alias_chain():
    first = worker
    second = first
    return second.transform(1)


def unknown_module_rebind(unknown_module):
    alias = worker
    alias = unknown_module
    return alias.transform(1)


def missing_module_member():
    alias = worker
    return alias.missing()


def package_import_capture():
    api = worker
    other = alternate
    return api.transform((api := other))


def package_import_capture_control():
    api = worker
    other = alternate
    return api.transform(other)


def external_import_capture():
    import external_a as api
    import external_b as other
    return api.work((api := other))


def call_external_direct():
    return external_worker.transform(1)


def call_external_alias():
    alias = external_worker
    return alias.transform(1)


def call_external_alias_chain():
    first = external_worker
    second = first
    return second.transform(1)


def call_external_overwrite(unknown):
    alias = external_worker
    alias = unknown
    return alias.transform(1)


def call_external_result():
    alias = external_worker.create()
    return alias.transform(1)


def call_external_extracted():
    alias, = external_worker
    return alias.transform(1)


def call_module_directly():
    return worker()


def call_reexported_module():
    from module_calls.entry import worker as imported_worker

    return imported_worker()


import module_calls.entry as current_module

self_call = current_module()
