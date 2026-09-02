from .ast import (
    Assignment, BinaryOp, Call, DictLiteral, EnumDef, ExprStmt, FieldAccess,
    ForLoop, FunctionDef, IfStmt, ListLiteral, Name, Number, Program,
    ReturnStmt, StringLiteral, StructDef, UnaryOp, UnionDef, VarDecl, WhileLoop,
)


class PythonCodeGenerator(object):
    def __init__(self):
        self.boxed_names = set()

    def find_addressed_names(self, node):
        names = set()
        if isinstance(node, (list, tuple)):
            for item in node:
                names.update(self.find_addressed_names(item))
            return names
        if isinstance(node, UnaryOp) and node.op == "&" and isinstance(node.value, Name):
            names.add(node.value.id)
        if hasattr(node, "__dict__"):
            for value in node.__dict__.values():
                if isinstance(value, list):
                    for item in value:
                        names.update(self.find_addressed_names(item))
                elif isinstance(value, tuple):
                    for item in value:
                        names.update(self.find_addressed_names(item))
                else:
                    names.update(self.find_addressed_names(value))
        return names

    def emit(self, node):
        if isinstance(node, Program):
            return "\n".join(self.emit(item) for item in node.items)
        if isinstance(node, FunctionDef):
            previous_boxed_names = self.boxed_names
            self.boxed_names = self.find_addressed_names(node.body)
            params = ", ".join(param.name for param in node.params)
            body = "\n".join("    " + line for line in self.emit_block(node.body).splitlines())
            signature = "def %s(%s):" % (node.name, params)
            boxed_params = [
                "    %s = _AutoCBox(%s)" % (param.name, param.name)
                for param in (param for param in node.params if param.name in self.boxed_names)
            ]
            if boxed_params:
                body = "\n".join(boxed_params + ([body] if body else []))
            self.boxed_names = previous_boxed_names
            return "%s\n%s" % (signature, body)
        if isinstance(node, (StructDef, UnionDef)):
            fields = ", ".join(name for name, _ in node.fields)
            assignments = "\n".join("        self.%s = %s" % (name, name) for name, _ in node.fields)
            return "class %s:\n    def __init__(self, %s):\n%s" % (node.name, fields, assignments)
        if isinstance(node, EnumDef):
            return "class %s:\n%s" % (
                node.name,
                "\n".join("    %s = %s" % (name, value) for name, value in node.members),
            )
        if isinstance(node, VarDecl):
            if node.value is None:
                return "%s = None" % node.name
            if node.name in self.boxed_names:
                return "%s = _AutoCBox(%s)" % (node.name, self.emit(node.value))
            return "%s = %s" % (node.name, self.emit(node.value))
        if isinstance(node, Assignment):
            if isinstance(node.target, UnaryOp) and node.target.op == "*":
                return "(%s).set(%s)" % (self.emit(node.target.value), self.emit(node.value))
            if node.target in self.boxed_names:
                return "%s.value = %s" % (node.target, self.emit(node.value))
            return "%s = %s" % (node.target, self.emit(node.value))
        if isinstance(node, ReturnStmt):
            if node.value is None:
                return "return"
            return "return %s" % self.emit(node.value)
        if isinstance(node, IfStmt):
            lines = ["if %s:" % self.emit(node.condition)]
            lines.extend("    " + line for line in self.emit_block(node.then_block).splitlines())
            if node.else_block is not None:
                lines.append("else:")
                lines.extend("    " + line for line in self.emit_block(node.else_block).splitlines())
            return "\n".join(lines)
        if isinstance(node, ForLoop):
            lines = ["for %s in %s:" % (node.var_name, self.emit(node.iterable))]
            lines.extend("    " + line for line in self.emit_block(node.body).splitlines())
            return "\n".join(lines)
        if isinstance(node, WhileLoop):
            lines = ["while %s:" % self.emit(node.condition)]
            lines.extend("    " + line for line in self.emit_block(node.body).splitlines())
            return "\n".join(lines)
        if isinstance(node, ExprStmt):
            return self.emit(node.expr)
        if isinstance(node, BinaryOp):
            return "(%s %s %s)" % (self.emit(node.left), node.op, self.emit(node.right))
        if isinstance(node, UnaryOp):
            if node.op == "&":
                if isinstance(node.value, Name) and node.value.id in self.boxed_names:
                    name = node.value.id
                    return "_AutoCPointer(lambda: %s.value, lambda new_value: setattr(%s, \"value\", new_value))" % (name, name)
                return "_AutoCPointer(lambda: %s)" % self.emit(node.value)
            if node.op == "*":
                return "(%s).get()" % self.emit(node.value)
            return "(%s%s)" % (node.op, self.emit(node.value))
        if isinstance(node, Call):
            args = ", ".join(self.emit(arg) for arg in node.args)
            return "%s(%s)" % (node.callee, args)
        if isinstance(node, Name):
            if node.id in self.boxed_names:
                return "%s.value" % node.id
            return node.id
        if isinstance(node, FieldAccess):
            return "%s.%s" % (self.emit(node.object_expr), node.field_name)
        if isinstance(node, Number):
            return str(node.value)
        if isinstance(node, StringLiteral):
            return repr(node.value)
        if isinstance(node, ListLiteral):
            return "[" + ", ".join(self.emit(item) for item in node.items) + "]"
        if isinstance(node, DictLiteral):
            pairs = ", ".join("%s: %s" % (self.emit(k), self.emit(v)) for k, v in node.items)
            return "{" + pairs + "}"
        raise TypeError("Unsupported node for Python generation: %s" % type(node).__name__)

    def emit_block(self, block):
        return "\n".join(self.emit(stmt) for stmt in block)

    def emit_program(self, program):
        code = self.emit(program)
        code = (
            "import math\n\n"
            "class _AutoCBox:\n"
            "    def __init__(self, value):\n"
            "        self.value = value\n\n"
            "class _AutoCPointer:\n"
            "    def __init__(self, getter, setter=None):\n"
            "        self._getter = getter\n"
            "        self._setter = setter\n"
            "    def get(self):\n"
            "        return self._getter()\n\n"
            "    def set(self, value):\n"
            "        if self._setter is None:\n"
            "            raise TypeError(\"pointer is read-only\")\n"
            "        self._setter(value)\n\n"
            "def malloc(size):\n"
            "    return bytearray(size)\n\n"
            "def free(value):\n"
            "    return None\n\n" + code
        )
        code = (
            "def strlen(value):\n"
            "    return len(value)\n\n"
            "def atoi(value):\n"
            "    return int(value)\n\n"
            "def atof(value):\n"
            "    return float(value)\n\n"
            "def puts(value):\n"
            "    print(value)\n\n"
            "def putchar(value):\n"
            "    print(value, end=\"\")\n\n"
            "def printf(format_string, *args):\n"
            "    print(format_string % args, end=\"\")\n\n"
            "def memset(buffer, value, count):\n"
            "    buffer[:count] = bytes([value]) * count\n"
            "    return buffer\n\n"
            "def memcpy(destination, source, count):\n"
            "    destination[:count] = source[:count]\n"
            "    return destination\n\n" + code
        )
        has_main = any(
            isinstance(item, FunctionDef) and item.name == "main"
            for item in program.items
        )
        if has_main:
            code += "\n\nif __name__ == \"__main__\":\n    main()"
        return code
