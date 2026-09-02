from .ast import BinaryOp, Call, ExprStmt, ForLoop, IfStmt, Name, Number, ReturnStmt, UnaryOp, VarDecl, WhileLoop


class LLVMCodeGenerator(object):
    def __init__(self):
        self.lines = []
        self.register = 0
        self.label = 0
        self.values = {}

    def next_register(self):
        self.register += 1
        return "%%r%d" % self.register

    def next_label(self, prefix):
        self.label += 1
        return "%s%d" % (prefix, self.label)

    def emit_program(self, program):
        return "\n\n".join(
            self.emit_function(item.name, item.params, item.return_type or "int", item.body)
            for item in program.items if hasattr(item, "body")
        )

    def emit_function(self, name, params, return_type, body):
        self.lines = []
        self.register = 0
        self.label = 0
        self.values = {param.name: ("%" + param.name, param.type_name or "int") for param in params}
        param_list = ", ".join("%s %%%s" % (self.map_type(param.type_name or "int"), param.name) for param in params)
        self.lines.append("define %s @%s(%s) {" % (self.map_type(return_type), name, param_list))
        self.lines.append("entry:")

        self.emit_block(body)
        if not self.lines[-1].lstrip().startswith(("ret ", "br ")):
            self.lines.append("  ret void" if return_type == "void" else "  ret %s 0" % self.map_type(return_type))

        self.lines.append("}")
        return "\n".join(self.lines)

    def emit_block(self, body):
        for statement in body:
            self.emit_statement(statement)

    def emit_statement(self, statement):
        if isinstance(statement, VarDecl):
            if statement.value is not None:
                self.values[statement.name] = self.emit_expr(statement.value)
            return
        if isinstance(statement, ExprStmt):
            self.emit_expr(statement.expr)
            return
        if isinstance(statement, ReturnStmt):
            if statement.value is None:
                self.lines.append("  ret void")
            else:
                value, type_name = self.emit_expr(statement.value)
                self.lines.append("  ret %s %s" % (self.map_type(type_name), value))
            return
        if hasattr(statement, "target"):
            self.values[statement.target] = self.emit_expr(statement.value)
            return
        if isinstance(statement, IfStmt):
            condition, _ = self.emit_expr(statement.condition)
            then_label = self.next_label("then")
            else_label = self.next_label("else") if statement.else_block is not None else None
            end_label = self.next_label("endif")
            self.lines.append("  br i1 %s, label %%%s, label %%%s" % (condition, then_label, else_label or end_label))
            self.lines.append("%s:" % then_label)
            self.emit_block(statement.then_block)
            self.lines.append("  br label %%%s" % end_label)
            if else_label:
                self.lines.append("%s:" % else_label)
                self.emit_block(statement.else_block)
                self.lines.append("  br label %%%s" % end_label)
            self.lines.append("%s:" % end_label)
            return
        if isinstance(statement, WhileLoop):
            condition_label = self.next_label("while")
            body_label = self.next_label("while_body")
            end_label = self.next_label("while_end")
            self.lines.append("  br label %%%s" % condition_label)
            self.lines.append("%s:" % condition_label)
            condition, _ = self.emit_expr(statement.condition)
            self.lines.append("  br i1 %s, label %%%s, label %%%s" % (condition, body_label, end_label))
            self.lines.append("%s:" % body_label)
            self.emit_block(statement.body)
            self.lines.append("  br label %%%s" % condition_label)
            self.lines.append("%s:" % end_label)
            return
        if isinstance(statement, ForLoop):
            iterable, _ = self.emit_expr(statement.iterable)
            self.lines.append("  ; for %s in %s" % (statement.var_name, iterable))
            return

    def emit_expr(self, expr):
        if isinstance(expr, Number):
            return (str(int(expr.value)) if isinstance(expr.value, bool) else str(expr.value), "bool" if isinstance(expr.value, bool) else ("float" if isinstance(expr.value, float) else "int"))
        if isinstance(expr, Name):
            return self.values.get(expr.id, ("0", "int"))
        if isinstance(expr, UnaryOp):
            value, type_name = self.emit_expr(expr.value)
            if expr.op == "!":
                result = self.next_register()
                self.lines.append("  %s = xor i1 %s, true" % (result, value))
                return result, "bool"
            return value, type_name
        if isinstance(expr, BinaryOp):
            left, left_type = self.emit_expr(expr.left)
            right, right_type = self.emit_expr(expr.right)
            type_name = "float" if "float" in {left_type, right_type} else "int"
            if expr.op in {"==", "!=", "<", ">", "<=", ">="}:
                predicate = {"==": "eq", "!=": "ne", "<": "slt", ">": "sgt", "<=": "sle", ">=": "sge"}[expr.op]
                result = self.next_register()
                self.lines.append("  %s = icmp %s i32 %s, %s" % (result, predicate, left, right))
                return result, "bool"
            operation = {"+": "add", "-": "sub", "*": "mul", "/": "sdiv", "%": "srem", "<<": "shl", ">>": "lshr", "&": "and", "|": "or", "^": "xor", "&&": "and", "||": "or"}.get(expr.op)
            if operation is None:
                return "0", "int"
            result = self.next_register()
            self.lines.append("  %s = %s %s %s, %s" % (result, operation, self.map_type(type_name), left, right))
            return result, type_name
        if isinstance(expr, Call):
            args = []
            for arg in expr.args:
                value, type_name = self.emit_expr(arg)
                args.append("%s %s" % (self.map_type(type_name), value))
            result = self.next_register()
            self.lines.append("  %s = call i32 @%s(%s)" % (result, expr.callee, ", ".join(args)))
            return result, "int"
        return "0", "int"
    def map_type(self, type_name):
        mapping = {
            "int": "i32",
            "char": "i8",
            "float": "double",
            "double": "double",
            "bool": "i1",
            "str": "i8*",
            "void": "void",
        }
        if type_name not in mapping:
            raise ValueError("Unsupported AutoC type: %s" % type_name)
        return mapping[type_name]
