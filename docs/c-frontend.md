# C Frontend

AutoC exposes a C99 parser through `autoc.c_frontend`:

```python
from autoc.c_frontend import parse_c, validate_c

tree = parse_c("int main(void) { return 0; }")
assert validate_c("int main(void) { return 0; }")
```

The frontend accepts C translation units and returns the standard pycparser
AST, including declarations, expressions, functions, arrays, pointers,
structs, unions, enums, and control flow. `compile_c_to_python` translates the
common executable subset into standalone Python and strips simple preprocessor
lines such as `#include`. Unsupported C constructs raise `CCodegenError`
instead of being silently changed.

`compile_c_to_llvm` lowers the same supported subset through AutoC's LLVM
backend. It currently targets integer arithmetic, calls, returns, and basic
control flow; unsupported C AST nodes raise `CLLVMError`.