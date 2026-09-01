from pathlib import Path

from .codegen_python import PythonCodeGenerator
from .lexer import tokenize
from .parser import parse_tokens


class AutoCCompileError(Exception):
    pass


def compile_autoc_to_python(source):
    tokens = tokenize(source)
    program = parse_tokens(tokens)
    generator = PythonCodeGenerator()
    return generator.emit_program(program)


def run_autoc_string(source):
    python_code = compile_autoc_to_python(source)
    ns = {}
    exec(python_code, ns, ns)
    return ns


def run_autoc_file(path):
    text = Path(path).read_text(encoding="utf-8")
    return run_autoc_string(text)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoC minimal interpreter")
    parser.add_argument("source", help="Path to .autoc source file")
    parser.add_argument("--emit-python", action="store_true", help="Print generated Python instead of executing")
    args = parser.parse_args()

    text = Path(args.source).read_text(encoding="utf-8")
    if args.emit_python:
        print(compile_autoc_to_python(text))
    else:
        ns = run_autoc_string(text)
        print(ns)


if __name__ == "__main__":
    main()
