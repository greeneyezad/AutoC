from typing import List


KEYWORDS = {
    "fn", "auto", "return", "if", "else", "for", "in", "while",
    "let", "true", "false", "print", "unsafe", "range",
    "int", "char", "float", "double", "bool", "str", "void", "list", "map",
    "struct", "union", "enum"
}

SINGLE_CHAR_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
    ":": "COLON",
    ";": "SEMI",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "=": "ASSIGN",
    "^": "CARET",
    "<": "LT",
    ">": "GT",
    "!": "BANG",
    "&": "AMP",
    "|": "PIPE",
    ".": "DOT",
}

DOUBLE_CHAR_TOKENS = {
    "==": "EQ",
    "!=": "NEQ",
    "<=": "LTE",
    ">=": "GTE",
    "&&": "ANDAND",
    "||": "OROR",
    "<<": "SHL",
    ">>": "SHR",
    "+=": "PLUS_ASSIGN",
    "-=": "MINUS_ASSIGN",
    "*=": "STAR_ASSIGN",
    "/=": "SLASH_ASSIGN",
    "%=": "PERCENT_ASSIGN",
    "&=": "AND_ASSIGN",
    "|=": "OR_ASSIGN",
    "^=": "XOR_ASSIGN",
}


class Token(object):
    def __init__(self, type, value, pos):
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self):
        return "Token(%s, %r, %s)" % (self.type, self.value, self.pos)


class LexerError(ValueError):
    pass


def tokenize(source):
    tokens = []
    i = 0
    length = len(source)

    while i < length:
        ch = source[i]

        if ch in " \t\r":
            i += 1
            continue

        if ch == "\n":
            i += 1
            continue

        if ch == "#":
            while i < length and source[i] != "\n":
                i += 1
            continue

        if ch in ('"', "'"):
            quote = ch
            start = i
            i += 1
            text = ""
            while i < length:
                current = source[i]
                if current == "\\":
                    i += 1
                    if i >= length:
                        raise LexerError("Unterminated string literal")
                    text += source[i]
                    i += 1
                    continue
                if current == quote:
                    i += 1
                    break
                text += current
                i += 1
            else:
                raise LexerError("Unterminated string literal")
            tokens.append(Token("STRING", text, start))
            continue

        if ch.isdigit():
            start = i
            while i < length and (source[i].isdigit() or source[i] == "."):
                i += 1
            digits = source[start:i]
            if digits.count(".") > 1:
                raise LexerError("Invalid number literal: %s" % digits)
            if "." in digits:
                tokens.append(Token("FLOAT", digits, start))
            else:
                tokens.append(Token("INT", digits, start))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < length and (source[i].isalnum() or source[i] == "_"):
                i += 1
            value = source[start:i]
            token_type = "KEYWORD" if value in KEYWORDS else "IDENT"
            tokens.append(Token(token_type, value, start))
            continue

        if i + 1 < length:
            pair = source[i:i + 2]
            if pair in DOUBLE_CHAR_TOKENS:
                tokens.append(Token(DOUBLE_CHAR_TOKENS[pair], pair, i))
                i += 2
                continue

        if ch in SINGLE_CHAR_TOKENS:
            tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, i))
            i += 1
            continue

        raise LexerError("Unexpected character: %r at position %s" % (ch, i))

    return tokens
