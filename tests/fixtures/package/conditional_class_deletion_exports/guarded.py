branch_value = branch_source
loop_value = loop_source
try_value = try_source
with_value = with_source
class_with_value = class_with_source

if first:
    if second:
        del branch_value

for item in items:
    class LoopClear:
        global loop_value
        del loop_value

try:
    class TryClear:
        global try_value
        del try_value
except Exception:
    pass

with manager:
    del with_value


class Publisher:
    global class_with_value
    with manager:
        del class_with_value
