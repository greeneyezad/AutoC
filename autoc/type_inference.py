from __future__ import annotations

from .ast import Assignment, BinaryOp, DictLiteral, ListLiteral, Name, Number, ReturnStmt, StringLiteral, VarDecl
from .lexer import tokenize
from .parser import parse_tokens


class TypeInferenceError(Exception):
    pass


def infer_types(source):
    program = parse_tokens(tokenize(source))

    def infer_expr(expr, scope):
        if isinstance(expr, Number):
            if isinstance(expr.value, bool):
                return "bool"
            if isinstance(expr.value, int):
                return "int"
            if isinstance(expr.value, float):
                return "float"
        if isinstance(expr, StringLiteral):
            return "str"
        if isinstance(expr, Name):
            return scope.get(expr.id, "auto")
        if isinstance(expr, ListLiteral):
            return "list"
        if isinstance(expr, DictLiteral):
            return "map"
        if isinstance(expr, BinaryOp):
            left_type = infer_expr(expr.left, scope)
            right_type = infer_expr(expr.right, scope)

            if left_type == "auto":
                return right_type
            if right_type == "auto":
                return left_type
            if left_type == "bool" and right_type == "bool":
                return "bool"
            if left_type in {"int", "float"} and right_type in {"int", "float"}:
                return "float" if "float" in {left_type, right_type} else "int"
            return "auto"
        return "auto"

    def walk_function(fn):
        scope = {}
        for param in fn.params:
            scope[param.name] = param.type_name or "auto"

        for stmt in fn.body:
            if isinstance(stmt, VarDecl):
                inferred = infer_expr(stmt.value, scope) if stmt.value is not None else "auto"
                stmt.inferred_type = inferred
                scope[stmt.name] = inferred
            elif isinstance(stmt, Assignment):
                if stmt.target in scope:
                    inferred = infer_expr(stmt.value, scope)
                    stmt.inferred_type = inferred
                    scope[stmt.target] = inferred
            elif isinstance(stmt, ReturnStmt):
                if stmt.value is not None:
                    stmt.inferred_type = infer_expr(stmt.value, scope)

    for item in program.items:
        if hasattr(item, "body"):
            walk_function(item)

    return program
