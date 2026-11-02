def main(value):
    if value == '"quoted"':
        return '"'
    return [value, r'C:\new\report', r'\N', 'line\nbreak']
