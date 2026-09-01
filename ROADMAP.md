# AutoC Roadmap

## Current status

AutoC is an early-stage compiler prototype. The parser, AST, Python backend, type inference, and LLVM-oriented IR generator are all in place for a minimal subset of the language.

## Near-term goals

### 1. Language stability
- Complete grammar support for the main statement forms
- Improve expression coverage and edge-case parsing
- Add stricter error messages and diagnostics

### 2. Type system
- Finish automatic inference for `auto` declarations and assignments
- Add explicit type-checking for function calls and returns
- Add optional static checking for invalid conversions

### 3. Ownership and memory safety
- Model borrowing and move semantics for arrays and maps
- Reject obvious invalid ownership patterns earlier in the pipeline
- Add scoped lifetime tracking for local variables

### 4. LLVM backend
- Generate valid IR for more than the simplest arithmetic case
- Support branch and loop lowering
- Add function-call lowering and stack allocation analysis

## Medium-term goals

- Support a richer statement set: `if`, `while`, nested blocks, and more
- Introduce a real module system and import model
- Add integration tests for parsing and semantic validation
- Build a more realistic benchmark harness comparing generated Python vs native targets

## Long-term vision

AutoC aims to become a practical systems-oriented language with:

- C-like execution performance
- Python-like ergonomics for tooling and code generation
- Rust-like safety defaults without excessive ceremony
- A compiler pipeline that can emit Python, LLVM IR, and eventually native machine code

## Milestones

- v0.1.0: public prototype with parser, AST, and Python backend
- v0.2.0: stable type inference and validation pipeline
- v0.3.0: ownership/lifetime checks integrated into the compiler
- v0.4.0: LLVM lowering for a larger subset of the language
- v1.0.0: first broadly usable release candidate
