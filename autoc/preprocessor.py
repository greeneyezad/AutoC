from pathlib import Path
import re


class PreprocessorError(ValueError):
    pass


DIRECTIVE = re.compile(r"^\s*#\s*(define|include|if|ifdef|ifndef|else|endif)\b(.*)$")
MACRO = re.compile(r"\b[A-Za-z_]\w*\b")
FUNCTION_MACRO = re.compile(r"^([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(.*)$")


def preprocess(source, base_dir=None, included=None, macros=None, include_paths=None):
    base = Path(base_dir) if base_dir is not None else Path.cwd()
    included = set() if included is None else included
    macros = {} if macros is None else macros
    include_paths = [Path(path) for path in (include_paths or [])]
    output = []
    conditions = []

    def is_active():
        return all(conditions)

    def expand(line):
        for _ in range(10):
            changed = False
            for name, value in macros.items():
                if isinstance(value, tuple):
                    parameters, body = value
                    pattern = re.compile(r"\b%s\s*\(([^()]*)\)" % re.escape(name))

                    def replace_function(match):
                        arguments = [item.strip() for item in match.group(1).split(",")]
                        if len(arguments) != len(parameters):
                            raise PreprocessorError("Macro %s expects %d arguments" % (name, len(parameters)))
                        result = body
                        for parameter, argument in zip(parameters, arguments):
                            result = re.sub(r"\b%s\b" % re.escape(parameter), argument, result)
                        return result

                    line, count = pattern.subn(replace_function, line)
                    changed = changed or count > 0
                else:
                    line, count = re.subn(r"\b%s\b" % re.escape(name), value, line)
                    changed = changed or count > 0
            if not changed:
                break
        return line

    for line in source.splitlines():
        match = DIRECTIVE.match(line)
        if match is None:
            if is_active():
                output.append(expand(line))
            continue

        directive, argument = match.groups()
        argument = argument.strip()
        if directive == "if":
            conditions.append(is_active() and expand(argument) not in {"0", "false", "False"})
            continue
        if directive in {"ifdef", "ifndef"}:
            defined = argument in macros
            conditions.append(is_active() and (defined if directive == "ifdef" else not defined))
            continue
        if directive == "else":
            if not conditions:
                raise PreprocessorError("#else without matching #if")
            parent_active = all(conditions[:-1])
            conditions[-1] = parent_active and not conditions[-1]
            continue
        if directive == "endif":
            if not conditions:
                raise PreprocessorError("#endif without matching #if")
            conditions.pop()
            continue
        if not is_active():
            continue
        if directive == "define":
            function_match = FUNCTION_MACRO.match(argument)
            if function_match is not None:
                name, parameters, value = function_match.groups()
                parameters = [item.strip() for item in parameters.split(",") if item.strip()]
                macros[name] = (parameters, value)
                continue
            parts = argument.split(None, 1)
            if len(parts) != 2 or not re.match(r"^[A-Za-z_]\w*$", parts[0]):
                raise PreprocessorError("#define requires a name and value")
            macros[parts[0]] = parts[1]
            continue

        header_match = re.match(r'^["<](.*?)[">]$', argument)
        if header_match is None:
            raise PreprocessorError("#include requires a quoted path")
        header_name = header_match.group(1)
        candidates = [base / header_name]
        if argument.startswith("<"):
            candidates.extend(path / header_name for path in include_paths)
        header = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
        if header is None:
            raise PreprocessorError("Header not found: %s" % header_name)
        if header in included:
            raise PreprocessorError("Circular include: %s" % header)
        included.add(header)
        output.append(preprocess(header.read_text(encoding="utf-8"), header.parent, included, macros, include_paths))

    if conditions:
        raise PreprocessorError("Unterminated conditional directive")

    return "\n".join(output)