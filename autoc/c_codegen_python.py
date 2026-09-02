from pycparser import c_ast


class CCodegenError(ValueError):
    pass


class CToPython:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def emit(self, tree):
        for node in tree.ext:
            if isinstance(node, c_ast.FuncDef):
                self.emit_function(node)
        if not self.lines:
            raise CCodegenError("C source contains no function definitions")
        if any(line.startswith("def main") for line in self.lines):
            self.lines.extend(["", "if __name__ == \"__main__\":", "    main()"])
        prelude = [
            "def printf(format_string, *args):",
            "    print(format_string % args, end=\"\")",
            "",
        ]
        return "\n".join(prelude + self.lines)

    def write(self, text):
        self.lines.append("    " * self.indent + text)

    def emit_function(self, node):
        parameters = []
        if node.decl.type.args:
            parameters = [parameter.name for parameter in node.decl.type.args.params if getattr(parameter, "name", None)]
        self.write("def %s(%s):" % (node.decl.name, ", ".join(parameters)))
        self.indent += 1
        self.emit_statement(node.body)
        if not self.lines[-1].lstrip().startswith("return"):
            self.write("return None")
        self.indent -= 1

    def emit_statement(self, node):
        if isinstance(node, c_ast.Compound):
            for item in node.block_items or []:
                self.emit_statement(item)
        elif isinstance(node, c_ast.Decl):
            value = "None" if node.init is None else self.expression(node.init)
            self.write("%s = %s" % (node.name, value))
        elif isinstance(node, c_ast.DeclList):
            for declaration in node.decls:
                self.emit_statement(declaration)
        elif isinstance(node, c_ast.Return):
            self.write("return %s" % (self.expression(node.expr) if node.expr else "None"))
        elif isinstance(node, c_ast.Assignment):
            self.write("%s %s %s" % (self.expression(node.lvalue), node.op, self.expression(node.rvalue)))
        elif isinstance(node, c_ast.FuncCall):
            self.write(self.expression(node))
        elif isinstance(node, c_ast.If):
            self.write("if %s:" % self.expression(node.cond))
            self.indent += 1
            self.emit_statement(node.iftrue)
            self.indent -= 1
            if node.iffalse:
                self.write("else:")
                self.indent += 1
                self.emit_statement(node.iffalse)
                self.indent -= 1
        elif isinstance(node, c_ast.While):
            self.write("while %s:" % self.expression(node.cond))
            self.indent += 1
            self.emit_statement(node.stmt)
            self.indent -= 1
        elif isinstance(node, c_ast.For):
            if node.init:
                self.emit_statement(node.init)
            self.write("while %s:" % (self.expression(node.cond) if node.cond else "True"))
            self.indent += 1
            self.emit_statement(node.stmt)
            if node.next:
                self.write(self.expression(node.next))
            self.indent -= 1
        elif isinstance(node, c_ast.EmptyStatement):
            self.write("pass")
        else:
            raise CCodegenError("Unsupported C statement: %s" % type(node).__name__)

    def expression(self, node):
        if isinstance(node, c_ast.Constant):
            if node.type == "string":
                return repr(node.value[1:-1])
            if node.type == "char":
                return repr(node.value[1:-1])
            return node.value
        if isinstance(node, c_ast.ID):
            return node.name
        if isinstance(node, c_ast.BinaryOp):
            operator = {"&&": "and", "||": "or"}.get(node.op, node.op)
            return "(%s %s %s)" % (self.expression(node.left), operator, self.expression(node.right))
        if isinstance(node, c_ast.UnaryOp):
            if node.op == "p++":
                return "%s += 1" % self.expression(node.expr)
            if node.op == "p--":
                return "%s -= 1" % self.expression(node.expr)
            return "(%s%s)" % (node.op, self.expression(node.expr))
        if isinstance(node, c_ast.Assignment):
            return "%s %s %s" % (self.expression(node.lvalue), node.op, self.expression(node.rvalue))
        if isinstance(node, c_ast.FuncCall):
            arguments = [] if node.args is None else [self.expression(argument) for argument in node.args.exprs]
            return "%s(%s)" % (self.expression(node.name), ", ".join(arguments))
        if isinstance(node, c_ast.ArrayRef):
            return "%s[%s]" % (self.expression(node.name), self.expression(node.subscript))
        if isinstance(node, c_ast.StructRef):
            return "%s.%s" % (self.expression(node.name), self.expression(node.field))
        if isinstance(node, c_ast.InitList):
            return "[%s]" % ", ".join(self.expression(item) for item in node.exprs)
        if isinstance(node, c_ast.ExprList):
            return ", ".join(self.expression(item) for item in node.exprs)
        if isinstance(node, c_ast.Cast):
            return self.expression(node.expr)
        raise CCodegenError("Unsupported C expression: %s" % type(node).__name__)


def compile_c_to_python(tree):
    return CToPython().emit(tree)
