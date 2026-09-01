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

1. Publish the current milestone and project metadata.
2. Maintain a roadmap for language stability and compiler features.
3. Add benchmark coverage to validate the prototype direction.
4. Continue work on ownership, type inference, and LLVM lowering.

## Benchmarks

A basic benchmark script is included in `benchmarks/benchmark_autoc.py` to measure the runtime of the current prototype on a representative loop-heavy workload.

## Roadmap

The project direction and milestones are tracked in `ROADMAP.md`.

## Status

This is an early prototype, not yet a production compiler. It is intentionally small, readable, and designed to be extended.
