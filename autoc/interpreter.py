from pathlib import Path

from .codegen_python import PythonCodeGenerator
from .lexer import tokenize
from .llvm_codegen import LLVMCodeGenerator
from .parser import parse_tokens
from .preprocessor import preprocess
from .type_inference import infer_types


class AutoCCompileError(Exception):
    pass


def compile_autoc_to_python(source, include_paths=None):
    source = preprocess(source, include_paths=include_paths)
    tokens = tokenize(source)
    program = parse_tokens(tokens)
    generator = PythonCodeGenerator()
    return generator.emit_program(program)


def compile_autoc_to_llvm(source):
    program = infer_types(source)
    generator = LLVMCodeGenerator()
    llvm = generator.emit_program(program)
    if not llvm:
        raise AutoCCompileError("No function found in AutoC source")
    return llvm


def run_autoc_string(source):
    python_code = compile_autoc_to_python(source)
    ns = {}
    exec(python_code, ns, ns)
    return ns


def run_autoc_file(path):
    source = Path(path)
    return run_autoc_string(preprocess(source.read_text(encoding="utf-8"), source.parent))


def compile_autoc_file(source_path, output_path, include_paths=None):
    source = Path(source_path)
    output = Path(output_path)
    text = preprocess(source.read_text(encoding="utf-8"), source.parent, include_paths=include_paths)
    output.write_text(compile_autoc_to_python(text), encoding="utf-8")
    return output


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compile and run AutoC programs")
    parser.add_argument("source", help="Path to .autoc source file")
    parser.add_argument("--emit-python", action="store_true", help="Print generated Python instead of executing")
    parser.add_argument("--emit-llvm", action="store_true", help="Print generated LLVM IR instead of executing")
    parser.add_argument("-o", "--output", help="Write generated Python to this path")
    parser.add_argument("--run", action="store_true", help="Run the source after compiling it")
    parser.add_argument("-I", "--include-dir", action="append", default=[], help="Add a header search directory")
    args = parser.parse_args()

    source = Path(args.source)
    text = preprocess(source.read_text(encoding="utf-8"), source.parent, include_paths=args.include_dir)
    if args.emit_python:
        print(compile_autoc_to_python(text))
    elif args.emit_llvm:
        print(compile_autoc_to_llvm(text))
    elif args.output:
        output = compile_autoc_file(args.source, args.output, args.include_dir)
        print("Compiled %s -> %s" % (args.source, output))
        if args.run:
            run_autoc_string(text)
    else:
        run_autoc_string(text)


if __name__ == "__main__":
    main()
