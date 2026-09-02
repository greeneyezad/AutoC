from typing import List

from .ast import (
    Assignment, BinaryOp, Call, DictLiteral, ExprStmt, ForLoop,
    EnumDef, FieldAccess, FunctionDef, IfStmt, ListLiteral, Name, Number, Param,
    Program, ReturnStmt, StringLiteral, UnaryOp, VarDecl, WhileLoop,
    StructDef, UnionDef,
)
from .lexer import Token


class ParserError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def peek(self, offset: int = 0):
        pos = self.index + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]

    def current(self):
        return self.peek(0)

    def advance(self):
        tok = self.current()
        if tok is not None:
            self.index += 1
        return tok

    def match(self, *names):
        tok = self.current()
        if tok is None:
            return False
        if tok.type in names or tok.value in names:
            self.index += 1
            return True
        return False

    def expect(self, *names):
        tok = self.current()
        if tok is None:
            raise ParserError(f"Expected one of {names}, got EOF")
        if tok.type in names or tok.value in names:
            self.index += 1
            return tok
        raise ParserError(f"Expected one of {names}, got {tok.type}={tok.value!r} at {tok.pos}")

    def parse(self) -> Program:
        items = []
        while self.current() is not None:
            items.append(self.parse_statement())
        return Program(items)

    def parse_statement(self):
        tok = self.current()
        if tok is None:
            raise ParserError("Unexpected EOF")

        if tok.type == "SEMI":
            self.advance()
            return self.parse_statement()
        if tok.type == "KEYWORD" and tok.value == "fn":
            return self.parse_function()
        if tok.type == "KEYWORD" and tok.value in {"struct", "union", "enum"}:
            return self.parse_type_definition()
        if tok.type == "KEYWORD" and tok.value == "return":
            return self.parse_return()
        if tok.type == "KEYWORD" and tok.value == "if":
            return self.parse_if()
        if tok.type == "KEYWORD" and tok.value == "for":
            return self.parse_for()
        if tok.type == "KEYWORD" and tok.value == "while":
            return self.parse_while()
        if tok.type == "KEYWORD" and tok.value in {"auto", "let"}:
            return self.parse_var_decl()
        if tok.type == "KEYWORD" and tok.value in {"int", "char", "float", "double", "bool", "str", "void"}:
            return self.parse_typed_decl()
        if tok.type == "KEYWORD" and tok.value in {"print", "range"}:
            return ExprStmt(self.parse_expression())

        if tok.type == "STAR":
            target = self.parse_unary()
            operator = self.advance()
            if operator is None or operator.type not in {"ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN"}:
                raise ParserError("Expected assignment operator after dereference")
            value = self.parse_expression()
            if operator.type != "ASSIGN":
                value = BinaryOp(operator.value[:-1], target, value)
            return Assignment(target, value)

        if tok.type == "IDENT":
            if self.peek(1) is not None and self.peek(1).type in {
                "ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN", "STAR_ASSIGN",
                "SLASH_ASSIGN", "PERCENT_ASSIGN", "AND_ASSIGN",
                "OR_ASSIGN", "XOR_ASSIGN",
            }:
                return self.parse_assignment()
            expr = self.parse_expression()
            return ExprStmt(expr)

        raise ParserError(f"Unexpected token: {tok}")

    def parse_function(self):
        self.expect("KEYWORD", "fn")
        name_tok = self.expect("IDENT")
        self.expect("LPAREN")
        params = []
        if self.current() is not None and self.current().type != "RPAREN":
            while True:
                param_name = self.expect("IDENT")
                type_name = None
                if self.match("COLON"):
                    type_name = self.parse_type_name()
                params.append(Param(param_name.value, type_name))
                if not self.match("COMMA"):
                    break
        self.expect("RPAREN")
        return_type = None
        if self.match("MINUS"):
            self.expect("GT")
            return_type = self.parse_type_name()
        body = self.parse_block()
        return FunctionDef(name_tok.value, params, return_type, body)

    def parse_block(self):
        self.expect("LBRACE")
        statements = []
        while self.current() is not None and self.current().type != "RBRACE":
            statements.append(self.parse_statement())
        self.expect("RBRACE")
        return statements

    def parse_type_definition(self):
        kind = self.advance().value
        name = self.expect("IDENT").value
        self.expect("LBRACE")
        if kind == "enum":
            members = []
            next_value = 0
            while self.current() is not None and self.current().type != "RBRACE":
                member = self.expect("IDENT").value
                value = next_value
                if self.match("ASSIGN"):
                    value = self.expect("INT").value
                    value = int(value)
                members.append((member, value))
                next_value = value + 1
                self.match("COMMA")
            self.expect("RBRACE")
            return EnumDef(name, members)

        fields = []
        while self.current() is not None and self.current().type != "RBRACE":
            field_type = self.parse_type_name()
            field_name = self.expect("IDENT").value
            fields.append((field_name, field_type))
            self.expect("SEMI")
        self.expect("RBRACE")
        return StructDef(name, fields) if kind == "struct" else UnionDef(name, fields)

    def parse_var_decl(self):
        self.expect("KEYWORD", "auto", "let")
        name_tok = self.expect("IDENT")
        type_name = None
        if self.match("COLON"):
            type_name = self.parse_type_name()
        self.expect("ASSIGN")
        value = self.parse_expression()
        return VarDecl(name_tok.value, value, type_name, auto=True)

    def parse_typed_decl(self):
        type_name = self.parse_type_name()
        name_tok = self.expect("IDENT")
        value = None
        if self.match("ASSIGN"):
            value = self.parse_expression()
        return VarDecl(name_tok.value, value, type_name, auto=False)

    def parse_assignment(self):
        name_tok = self.expect("IDENT")
        operator = self.advance()
        if operator is None or operator.type not in {
            "ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN", "STAR_ASSIGN",
            "SLASH_ASSIGN", "PERCENT_ASSIGN", "AND_ASSIGN",
            "OR_ASSIGN", "XOR_ASSIGN",
        }:
            raise ParserError("Expected assignment operator")
        value = self.parse_expression()
        if operator.type != "ASSIGN":
            value = BinaryOp(operator.value[:-1], Name(name_tok.value), value)
        return Assignment(name_tok.value, value)

    def parse_return(self):
        self.expect("KEYWORD", "return")
        if self.current() is None or self.current().type == "RBRACE":
            return ReturnStmt(None)
        return ReturnStmt(self.parse_expression())

    def parse_if(self):
        self.expect("KEYWORD", "if")
        condition = self.parse_expression()
        then_block = self.parse_block()
        else_block = None
        if self.current() is not None and self.current().type == "KEYWORD" and self.current().value == "else":
            self.expect("KEYWORD", "else")
            else_block = self.parse_block()
        return IfStmt(condition, then_block, else_block)

    def parse_for(self):
        self.expect("KEYWORD", "for")
        auto_infer = self.match("KEYWORD", "auto")
        var_name = self.expect("IDENT").value
        self.expect("KEYWORD", "in")
        iterable = self.parse_expression()
        body = self.parse_block()
        return ForLoop(var_name, iterable, body)

    def parse_while(self):
        self.expect("KEYWORD", "while")
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileLoop(condition, body)

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.current() is not None and self.current().type == "OROR":
            op = self.advance().value
            right = self.parse_and()
            left = BinaryOp(op, left, right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.current() is not None and self.current().type == "ANDAND":
            op = self.advance().value
            right = self.parse_equality()
            left = BinaryOp(op, left, right)
        return left

    def parse_equality(self):
        left = self.parse_bitwise_or()
        while self.current() is not None and self.current().type in {"EQ", "NEQ"}:
            op = self.advance().value
            right = self.parse_bitwise_or()
            left = BinaryOp(op, left, right)
        return left

    def parse_bitwise_or(self):
        left = self.parse_bitwise_xor()
        while self.current() is not None and self.current().type == "PIPE":
            op = self.advance().value
            left = BinaryOp(op, left, self.parse_bitwise_xor())
        return left

    def parse_bitwise_xor(self):
        left = self.parse_bitwise_and()
        while self.current() is not None and self.current().type == "CARET":
            op = self.advance().value
            left = BinaryOp(op, left, self.parse_bitwise_and())
        return left

    def parse_bitwise_and(self):
        left = self.parse_relational()
        while self.current() is not None and self.current().type == "AMP":
            op = self.advance().value
            left = BinaryOp(op, left, self.parse_relational())
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.current() is not None and self.current().type in {"LT", "GT", "LTE", "GTE"}:
            op = self.advance().value
            right = self.parse_additive()
            left = BinaryOp(op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_shift()
        while self.current() is not None and self.current().type in {"PLUS", "MINUS"}:
            op = self.advance().value
            right = self.parse_shift()
            left = BinaryOp(op, left, right)
        return left

    def parse_shift(self):
        left = self.parse_multiplicative()
        while self.current() is not None and self.current().type in {"SHL", "SHR"}:
            op = self.advance().value
            left = BinaryOp(op, left, self.parse_multiplicative())
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.current() is not None and self.current().type in {"STAR", "SLASH", "PERCENT"}:
            if (
                self.current().type == "STAR"
                and self.peek(1) is not None
                and self.peek(1).type == "IDENT"
                and self.peek(2) is not None
                and self.peek(2).type in {"ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN"}
            ):
                break
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(op, left, right)
        return left

    def parse_unary(self):
        if self.current() is not None and self.current().type in {"PLUS", "MINUS", "BANG", "AMP", "STAR"}:
            op = self.advance().value
            return UnaryOp(op, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()
        if tok is None:
            raise ParserError("Unexpected EOF in expression")

        if tok.type == "INT":
            self.advance()
            return Number(int(tok.value))
        if tok.type == "FLOAT":
            self.advance()
            return Number(float(tok.value))
        if tok.type == "STRING":
            self.advance()
            return StringLiteral(tok.value)
        if tok.type == "KEYWORD" and tok.value == "true":
            self.advance()
            return Number(True)
        if tok.type == "KEYWORD" and tok.value == "false":
            self.advance()
            return Number(False)
        if tok.type == "KEYWORD" and tok.value in {"print", "range"}:
            name = self.advance().value
            self.expect("LPAREN")
            args = []
            if self.current() is not None and self.current().type != "RPAREN":
                while True:
                    args.append(self.parse_expression())
                    if not self.match("COMMA"):
                        break
            self.expect("RPAREN")
            return Call(name, args)

        if tok.type == "IDENT":
            name = self.advance().value
            if self.match("LPAREN"):
                args = []
                if self.current() is not None and self.current().type != "RPAREN":
                    while True:
                        args.append(self.parse_expression())
                        if not self.match("COMMA"):
                            break
                self.expect("RPAREN")
                return Call(name, args)
            expression = Name(name)
            while self.match("DOT"):
                expression = FieldAccess(expression, self.expect("IDENT").value)
            return expression

        if self.match("LPAREN"):
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr

        if self.match("LBRACKET"):
            items = []
            if self.current() is not None and self.current().type != "RBRACKET":
                while True:
                    items.append(self.parse_expression())
                    if not self.match("COMMA"):
                        break
            self.expect("RBRACKET")
            return ListLiteral(items)

        if self.match("LBRACE"):
            items = []
            if self.current() is not None and self.current().type != "RBRACE":
                while True:
                    key = self.parse_expression()
                    self.expect("COLON")
                    value = self.parse_expression()
                    items.append((key, value))
                    if not self.match("COMMA"):
                        break
            self.expect("RBRACE")
            return DictLiteral(items)

        raise ParserError(f"Unexpected token in expression: {tok}")

    def parse_type_name(self):
        tok = self.current()
        if tok is None:
            raise ParserError("Missing type name")
        if tok.type == "IDENT" or (tok.type == "KEYWORD" and tok.value in {"int", "char", "float", "double", "bool", "str", "void", "list", "map"}):
            self.advance()
            return tok.value
        raise ParserError(f"Invalid type name: {tok}")


def parse_tokens(tokens: List[Token]):
    parser = Parser(tokens)
    return parser.parse()
