from pathlib import Path
import re


class PreprocessorError(ValueError):
    pass


DIRECTIVE = re.compile(r"^\s*#\s*(define|include)\b(.*)$")
MACRO = re.compile(r"\b[A-Za-z_]\w*\b")


def preprocess(source, base_dir=None, included=None, macros=None):
    base = Path(base_dir) if base_dir is not None else Path.cwd()
    included = set() if included is None else included
    macros = {} if macros is None else macros
    output = []

    for line in source.splitlines():
        match = DIRECTIVE.match(line)
        if match is None:
            output.append(MACRO.sub(lambda token: macros.get(token.group(0), token.group(0)), line))
            continue

        directive, argument = match.groups()
        if directive == "define":
            parts = argument.strip().split(None, 1)
            if len(parts) != 2 or not re.match(r"^[A-Za-z_]\w*$", parts[0]):
                raise PreprocessorError("#define requires a name and value")
            macros[parts[0]] = parts[1]
            continue

        header_match = re.match(r'^\s*["<](.*?)[">]\s*$', argument)
        if header_match is None:
            raise PreprocessorError("#include requires a quoted path")
        header = (base / header_match.group(1)).resolve()
        if header in included:
            raise PreprocessorError("Circular include: %s" % header)
        if not header.is_file():
            raise PreprocessorError("Header not found: %s" % header)
        included.add(header)
        output.append(preprocess(header.read_text(encoding="utf-8"), header.parent, included, macros))

    return "\n".join(output)