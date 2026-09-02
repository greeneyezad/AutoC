from .ast import Call, DictLiteral, ListLiteral, Name, VarDecl
from .lexer import tokenize
from .parser import parse_tokens


class OwnershipError(Exception):
    pass


def check_ownership(source):
    program = parse_tokens(tokenize(source))

    def is_owned_value(expr):
        return isinstance(expr, (ListLiteral, DictLiteral)) or (
            isinstance(expr, Call) and expr.callee == "malloc"
        )

    def names_used(expr):
        if isinstance(expr, Name):
            return [expr.id]
        if isinstance(expr, Call):
            names = []
            for arg in expr.args:
                names.extend(names_used(arg))
            return names
        if hasattr(expr, "left") and hasattr(expr, "right"):
            return names_used(expr.left) + names_used(expr.right)
        if hasattr(expr, "value") and not isinstance(expr, (ListLiteral, DictLiteral)):
            return names_used(expr.value)
        if isinstance(expr, ListLiteral):
            names = []
            for item in expr.items:
                names.extend(names_used(item))
            return names
        if isinstance(expr, DictLiteral):
            names = []
            for key, value in expr.items:
                names.extend(names_used(key))
                names.extend(names_used(value))
            return names
        return []

    def validate_uses(expr, owned, moved, freed):
        for name in names_used(expr):
            if name in moved or name in freed:
                raise OwnershipError("Use of moved or freed variable: %s" % name)

    def walk_block(block, owned, moved, freed):
        for statement in block:
            expression = getattr(statement, "expr", None)
            if expression is not None:
                validate_uses(expression, owned, moved, freed)
                if isinstance(expression, Call) and expression.callee == "free":
                    if len(expression.args) != 1 or not isinstance(expression.args[0], Name):
                        raise OwnershipError("free() requires one owned variable")
                    name = expression.args[0].id
                    if name in freed or name not in owned:
                        raise OwnershipError("Cannot free unowned variable: %s" % name)
                    freed.add(name)
                    owned.remove(name)
                continue

            if isinstance(statement, VarDecl) and statement.value is not None:
                validate_uses(statement.value, owned, moved, freed)
                if isinstance(statement.value, Name) and statement.value.id in owned:
                    source_name = statement.value.id
                    owned.remove(source_name)
                    moved.add(source_name)
                    owned.add(statement.name)
                elif is_owned_value(statement.value):
                    owned.add(statement.name)
                continue

            if hasattr(statement, "value") and statement.value is not None:
                validate_uses(statement.value, owned, moved, freed)
            if hasattr(statement, "then_block"):
                walk_block(statement.then_block, set(owned), set(moved), set(freed))
                if statement.else_block is not None:
                    walk_block(statement.else_block, set(owned), set(moved), set(freed))
            if hasattr(statement, "body"):
                walk_block(statement.body, set(owned), set(moved), set(freed))

    for item in program.items:
        if hasattr(item, "body"):
            walk_block(item.body, set(), set(), set())
    return True
