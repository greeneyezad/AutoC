from typing import Any, List, Optional, Tuple


class Node(object):
    pass


class Program(Node):
    def __init__(self, items=None):
        self.items = items if items is not None else []


class FunctionDef(Node):
    def __init__(self, name, params, return_type, body):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body


class Param(Node):
    def __init__(self, name, type_name=None):
        self.name = name
        self.type_name = type_name


class VarDecl(Node):
    def __init__(self, name, value=None, type_name=None, auto=False):
        self.name = name
        self.value = value
        self.type_name = type_name
        self.auto = auto
        self.inferred_type = None


class Assignment(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value
        self.inferred_type = None


class ReturnStmt(Node):
    def __init__(self, value=None):
        self.value = value
        self.inferred_type = None


class IfStmt(Node):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


class ForLoop(Node):
    def __init__(self, var_name, iterable, body):
        self.var_name = var_name
        self.iterable = iterable
        self.body = body


class WhileLoop(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class ExprStmt(Node):
    def __init__(self, expr):
        self.expr = expr


class BinaryOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class UnaryOp(Node):
    def __init__(self, op, value):
        self.op = op
        self.value = value


class Call(Node):
    def __init__(self, callee, args):
        self.callee = callee
        self.args = args


class Name(Node):
    def __init__(self, id):
        self.id = id


class Number(Node):
    def __init__(self, value):
        self.value = value


class StringLiteral(Node):
    def __init__(self, value):
        self.value = value


class ListLiteral(Node):
    def __init__(self, items):
        self.items = items


class DictLiteral(Node):
    def __init__(self, items):
        self.items = items


Expr = Node
