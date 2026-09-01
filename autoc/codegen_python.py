from .ast import (
    Assignment, BinaryOp, Call, DictLiteral, ExprStmt, ForLoop,
    FunctionDef, IfStmt, ListLiteral, Name, Number, Program, ReturnStmt,
    StringLiteral, UnaryOp, VarDecl, WhileLoop,
)


class PythonCodeGenerator(object):
    def emit(self, node):
        if isinstance(node, Program):
            return "\n".join(self.emit(item) for item in node.items)
        if isinstance(node, FunctionDef):
            params = ", ".join(param.name for param in node.params)
            body = "\n".join("    " + line for line in self.emit_block(node.body).splitlines())
            signature = "def %s(%s):" % (node.name, params)
            return "%s\n%s" % (signature, body)
        if isinstance(node, VarDecl):
            if node.value is None:
                return "%s = None" % node.name
            return "%s = %s" % (node.name, self.emit(node.value))
        if isinstance(node, Assignment):
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
            return "(%s%s)" % (node.op, self.emit(node.value))
        if isinstance(node, Call):
            args = ", ".join(self.emit(arg) for arg in node.args)
            return "%s(%s)" % (node.callee, args)
        if isinstance(node, Name):
            return node.id
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
        return self.emit(program)
