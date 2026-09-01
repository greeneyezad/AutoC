# AutoC

AutoC is a lightweight language concept that combines:

- C-like performance model
- Perl-like convenience syntax
- Rust-like safety defaults
- Python-friendly AST and code generation

This repository contains a minimal prototype: a tokenizer, parser, AST, and Python code generator for a small AutoC subset.

## Language goals

- Replace manual memory management with ownership and scoped lifetimes
- Eliminate undefined behavior through safe defaults
- Make type inference ergonomic with `auto`
- Keep syntax close to C and Perl for systems-style code
- Generate Python code from the same AST for debugging and tooling

## Supported subset

```autoc
fn add(a: int, b: int) -> int {
    auto total = a + b
    return total
}

fn main() {
    auto xs = [1, 2, 3, 4]
    auto total = 0
    for auto x in xs {
        total = total + x
    }
    print(add(total, 5))
}
```

## Project layout

- `autoc/lexer.py` - tokenizes the source
- `autoc/parser.py` - parses a minimal language grammar
- `autoc/ast.py` - AST node definitions
- `autoc/codegen_python.py` - emits Python source from the AST
- `autoc/interpreter.py` - compiles and runs AutoC source

## Running the interpreter

```bash
python -m autoc examples/hello.autoc
```

Or emit Python:

```bash
python -m autoc examples/hello.autoc --emit-python
```

## GitHub next steps

1. Create a new GitHub repository.
2. Commit the project.
3. Add a short project description and README.
4. Add a `LICENSE` file.
5. Create a `releases` milestone for v0.1.
6. Add issues for parser improvements, type inference, and LLVM backend work.

## Status

This is an early prototype, not yet a production compiler. It is intentionally small, readable, and designed to be extended.
