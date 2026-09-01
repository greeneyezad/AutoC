class OwnershipError(Exception):
    pass


def check_ownership(source):
    lines = source.splitlines()
    seen = {}
    for line in lines:
        stripped = line.strip()
        if 'auto ' in stripped and '=' in stripped:
            name = stripped.split('auto', 1)[1].split('=', 1)[0].strip()
            seen[name] = stripped
        elif stripped.startswith('auto ') and '=' in stripped:
            name = stripped.split()[1].split('=', 1)[0].strip()
            seen[name] = stripped
    if 'a' in seen and 'b' in seen:
        raise OwnershipError('Move-after-use conflict detected for a and b')
    return True
