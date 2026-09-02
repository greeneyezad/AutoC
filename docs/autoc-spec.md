# AutoC language specification

## 1. Goal

AutoC is a systems-oriented language designed to combine:

- C-like performance and syntax
- Perl-like ergonomics for arrays, hashes, and convenience expressions
- Rust-like safety defaults
- Python-friendly AST/code generation

The language is designed for safe systems programming without losing predictable runtime behavior.

## 2. Core principles

1. No manual memory management in normal code.
2. No undefined behavior by default.
3. `auto` is the default local declaration style.
4. Safe references are preferred over raw pointers.
5. Bounds checks and overflow checks are enforced in debug mode.
6. The compiler lowers to a fast backend, and the same AST can emit Python for tooling and debugging.

## 3. Lexical model

### Comments

- `#` starts a line comment.
- `#define NAME value` defines an object-like macro.
- `#define NAME(args) value` defines a function-like macro.
- `#include "file.autoc"` includes a file relative to the current source file.
- `#include <file.autoc>` searches the source directory and `-I` include paths.
- `#if`, `#ifdef`, `#ifndef`, `#else`, and `#endif` select conditional source.

Macro expansion is intentionally limited to object-like and simple
function-like macros; token pasting and stringification are not supported.

### Keywords

- `fn`, `auto`, `let`, `return`, `if`, `else`, `for`, `in`, `while`, `true`, `false`, `print`, `unsafe`, `range`

### Literals

- integers: `42`
- floats: `3.14`
- strings: `"hello"` or `'hello'`
- lists: `[1, 2, 3]`
- maps: `{ "a": 1, "b": 2 }`

## 4. Types

Built-in types include:

- `int`
- `char`
- `float`
- `double`
- `bool`
- `str`
- `void` for functions that do not return a value
- `list[T]`
- `map[K, V]`

Structs, unions, and enums are supported by the prototype Python backend:

```autoc
struct Point {
    int x;
    int y;
}

enum Color { RED, GREEN = 4, BLUE }
```

Struct and union values use Python objects during interpretation. Union storage
and C ABI layout are reserved for the native backend.

The Python backend provides managed pointer reads with `&value` and `*pointer`,
plus `malloc(size)` and `free(value)` helpers. Raw pointer arithmetic and writes
through dereferenced pointers require the native backend.

The language supports inferred local type declarations using `auto`:

```autoc
auto x = 10
auto xs = [1, 2, 3]
auto person = { "name": "Ada", "age": 36 }
```

## 5. Function model

```autoc
fn add(a: int, b: int) -> int {
    auto total = a + b
    return total
}
```

Rules:

- functions are declared with `fn`
- parameters may have explicit types or use inference where possible
- return type is optional when inferable
- bodies use braces

## 6. Control flow

### If statements

```autoc
if x > 0 {
    print("positive")
} else {
    print("non-positive")
}
```

### For loops

```autoc
for auto x in xs {
    print(x)
}
```

### While loops

```autoc
while count < 10 {
    count = count + 1
}
```

## 7. Memory and safety model

### Safe defaults

- No raw pointer arithmetic in normal code.
- No implicit nulls.
- `unsafe` blocks are permitted only for system interop.
- Variables are stack-allocated when possible.
- Large or long-lived objects may be allocated in arenas.

### Ownership

AutoC uses a simplified ownership model:

- one owner for each heap-managed object
- move semantics for large objects
- immutable borrow by default for shared access
- mutable borrow requires explicit mark

This is intentionally simpler than Rust but consistent with the safety goal.

The ownership checker tracks list, map, and `malloc` results. Assigning one of
these values to another variable moves ownership; using the original afterward
is rejected. `free` consumes an owned allocation and double-free or freeing an
unowned value is rejected.

## 8. Type inference

The compiler infers variable types from initial values. For example:

```autoc
auto x = 4
auto y = 3.5
auto z = [x, y]
```

Type inference is allowed for locals and returns where the type is unambiguous.

## 9. Python compatibility

AutoC is designed to be compatible with a Python code generator.

This creates a practical workflow:

1. write AutoC source
2. parse into an AST
3. emit Python for debugging and validation
4. later lower the AST to LLVM/IR for optimized native code

## 10. Example program

```autoc
fn fib(n: int) -> int {
    auto a = 1
    auto b = 1

    for auto i in range(2, n) {
        auto next = a + b
        a = b
        b = next
    }

    return a
}

fn main() {
    auto xs = [1, 2, 3, 4, 5]
    auto total = 0
    for auto x in xs {
        total = total + x
    }
    print(fib(10))
    print(total)
}
```

## 11. Compatibility target

AutoC is not a drop-in replacement for C or Python. It is a deliberately constrained systems language with:

- high-level convenience
- low-level execution semantics
- safe-by-default behavior
- Python transformation support

This makes it viable as a prototype compiler project and a realistic future language design.
