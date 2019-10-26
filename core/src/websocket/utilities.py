def ws_commands_extractor(data: str):
    if not data:
        return '', []
    _s = [x for x in data.strip().split(' ') if x]
    if len(_s) > 1:
        return _s[0], _s[1:]
    return _s[0], []
