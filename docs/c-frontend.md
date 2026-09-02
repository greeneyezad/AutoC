# C Frontend

AutoC exposes a C99 parser through `autoc.c_frontend`:

```python
from autoc.c_frontend import parse_c, validate_c

tree = parse_c("int main(void) { return 0; }")
assert validate_c("int main(void) { return 0; }")
```

The frontend accepts C translation units and returns the standard pycparser
AST, including declarations, expressions, functions, arrays, pointers,
structs, unions, enums, and control flow. It expects preprocessor directives
to be expanded before parsing. Translation from this C AST into AutoC's typed
AST and native LLVM ABI is the next frontend stage.