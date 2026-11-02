def main(flag, old, new):
    overwritten_after_condition = old
    if flag:
        overwritten_after_condition = new
    overwritten_after_condition = 0

    condition_after_overwrite = old
    condition_after_overwrite = 0
    if flag:
        condition_after_overwrite = new

    return overwritten_after_condition, condition_after_overwrite
