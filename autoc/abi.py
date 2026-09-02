from .lexer import tokenize
from .parser import parse_tokens
from .ast import FunctionDef


class ABIError(ValueError):
    pass


TYPE_MAP = {
    "void": "void",
    "bool": "_Bool",
    "char": "char",
    "int": "int32_t",
    "float": "float",
    "double": "double",
    "str": "const char *",
    "list": "void *",
    "map": "void *",
}


def c_type(type_name):
    if type_name in TYPE_MAP:
        return TYPE_MAP[type_name]
    raise ABIError("Cannot expose AutoC type in C ABI: %s" % type_name)


def generate_c_header(source, guard="AUTOC_GENERATED_H"):
    program = parse_tokens(tokenize(source))
    functions = [item for item in program.items if isinstance(item, FunctionDef)]
    if not functions:
        raise ABIError("No functions available for C ABI header")
    lines = [
        "#ifndef %s" % guard,
        "#define %s" % guard,
        "",
        "#include <stdint.h>",
        "",
    ]
    for function in functions:
        params = []
        for parameter in function.params:
            params.append("%s %s" % (c_type(parameter.type_name or "int"), parameter.name))
        lines.append("%s %s(%s);" % (c_type(function.return_type or "int"), function.name, ", ".join(params) or "void"))
    lines.extend(["", "#endif", ""])
    return "\n".join(lines)
