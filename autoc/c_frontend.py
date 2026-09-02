from pathlib import Path

from pycparser import c_ast, c_parser


class CFrontendError(ValueError):
    pass


class CFrontend:
    def __init__(self):
        self.parser = c_parser.CParser()

    def parse(self, source, filename="<string>"):
        if any(line.lstrip().startswith("#") for line in source.splitlines()):
            raise CFrontendError(
                "C preprocessor directives must be expanded before parsing"
            )
        try:
            return self.parser.parse(source, filename=filename)
        except c_parser.ParseError as error:
            raise CFrontendError("C parse error in %s: %s" % (filename, error)) from error


def parse_c(source, filename="<string>"):
    return CFrontend().parse(source, filename)


def parse_c_file(path):
    source = Path(path)
    return parse_c(source.read_text(encoding="utf-8"), str(source))


def validate_c(source, filename="<string>"):
    tree = parse_c(source, filename)
    return isinstance(tree, c_ast.FileAST)


def compile_c_to_python(source, filename="<string>"):
    from .c_codegen_python import compile_c_to_python as generate_python

    clean_source = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    return generate_python(parse_c(clean_source, filename))


def compile_c_to_llvm(source, filename="<string>"):
    from .c_codegen_llvm import compile_c_to_llvm as generate_llvm

    clean_source = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    return generate_llvm(parse_c(clean_source, filename))


if __name__ == "__main__":
    import argparse
    from pycparser import c_generator

    parser = argparse.ArgumentParser(description="Parse and normalize a C source file")
    parser.add_argument("source", help="Path to a preprocessed C source file")
    args = parser.parse_args()
    tree = parse_c_file(args.source)
    print(c_generator.CGenerator().visit(tree))
