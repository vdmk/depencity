def main(obj, values, pairs):
    attributes = [obj.value for obj.value in values]
    subscripts = {obj[0] for obj[0] in values}
    unpacked = {obj.value: obj[0] for (obj.value, obj[0]) in pairs}
    generated = (obj.value for obj.value in values)
    return attributes, subscripts, unpacked, generated
