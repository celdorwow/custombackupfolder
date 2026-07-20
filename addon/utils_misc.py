def version2str(value: str|tuple[int, int, int]):
    if isinstance(value, str):
        return value
    return ".".join(map(lambda x: str(x), value))


def get_formated_size(size):
    kb = 1024
    mb = kb*1024
    gb = mb*1024
    if size > gb:
        return f"{round(size/gb, 1)} GB"
    elif size > mb:
        return f"{round(size/mb, 1)} MB"
    elif size > kb:
        return f"{round(size/kb,1)} kB"
    else:
        return f"{size} bytes"
