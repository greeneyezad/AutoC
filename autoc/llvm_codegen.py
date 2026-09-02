class LLVMCodeGenerator(object):
    def __init__(self):
        self.lines = []

    def emit_function(self, name, params, return_type, body):
        self.lines = []
        param_list = ", ".join(f"{self.map_type(param.type_name or 'int')} %{param.name}" for param in params)
        self.lines.append(f"define {self.map_type(return_type)} @{name}({param_list}) {{")
        self.lines.append("entry:")

        for stmt in body:
            if getattr(stmt, "__class__", None).__name__ == "VarDecl":
                if hasattr(stmt.value, "op") and hasattr(stmt.value, "left") and hasattr(stmt.value, "right"):
                    left = self._expr_name(stmt.value.left)
                    right = self._expr_name(stmt.value.right)
                    self.lines.append(f"  %{stmt.name} = add nsw {self.map_type(stmt.inferred_type or 'int')} {left}, {right}")
                    continue
                if hasattr(stmt.value, "id"):
                    self.lines.append(f"  %{stmt.name} = add nsw i32 %{stmt.value.id}, 0")

        for stmt in body:
            if getattr(stmt, "__class__", None).__name__ == "ReturnStmt":
                if return_type == "void":
                    self.lines.append("  ret void")
                else:
                    value = self._expr_name(stmt.value) if stmt.value is not None else "0"
                    self.lines.append(f"  ret {self.map_type(return_type)} {value}")
                break
        else:
            if return_type == "void":
                self.lines.append("  ret void")
            else:
                self.lines.append(f"  ret {self.map_type(return_type)} 0")

        self.lines.append("}")
        return "\n".join(self.lines)

    def _expr_name(self, expr):
        if hasattr(expr, "id"):
            return f"%{expr.id}"
        if hasattr(expr, "value"):
            return str(expr.value)
        if hasattr(expr, "name"):
            return f"%{expr.name}"
        return "0"

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
