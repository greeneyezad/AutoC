# Contributing to AutoC

Thanks for helping improve AutoC.

## Development setup

1. Clone the repository.
2. Create a Python 3.12 environment.
3. Install development dependencies:

```bash
python -m pip install pytest
```

4. Run the test suite:

```bash
python -m pytest -q
```

## Project goals

AutoC is an experimental language prototype combining:

- C-inspired syntax
- Perl-like ergonomics
- Rust-like safety defaults
- Python-compatible AST/code generation

## Workflow

- Keep changes focused and easy to review.
- Prefer simple, testable compiler pipeline improvements.
- Add or update tests whenever behavior changes.
- Aim for readable AST and code-generation logic.

## Pull requests

- Keep titles descriptive.
- Include a short summary of the problem and solution.
- Mention tests run.
- Keep compiler/backend work grounded in concrete examples.

## Notes

This project is still an experimental prototype. The main priorities are:

- parser stability
- type inference correctness
- ownership/lifetime validation
- LLVM backend feasibility
