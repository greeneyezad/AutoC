import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from autoc.interpreter import compile_autoc_to_python, run_autoc_string, compile_autoc_to_llvm
from autoc.type_inference import infer_types, TypeInferenceError
from autoc.ownership import OwnershipError, check_ownership
from autoc.preprocessor import preprocess
from autoc.native import find_compiler, normalize_target
from autoc.c_frontend import compile_c_to_llvm, compile_c_to_python, parse_c, validate_c


def test_compile_autoc_to_python():
    src = '''
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
    '''
    output = compile_autoc_to_python(src)
    assert "def add" in output
    assert "for x in xs" in output
    assert "print(add(total, 5))" in output


def test_run_autoc_string():
    src = '''
    fn main() {
        auto xs = [1, 2, 3]
        auto total = 0
        for auto x in xs {
            total = total + x
        }
        print(total)
    }
    '''
    ns = run_autoc_string(src)
    assert "main" in ns


def test_type_inference_infers_values():
    src = '''
    fn add(a: int, b: int) -> int {
        auto total = a + b
        return total
    }
    '''
    program = infer_types(src)
    assert program.items[0].name == "add"
    assert program.items[0].body[0].inferred_type == "int"


def test_ownership_rejects_move_after_use():
    src = '''
    fn main() {
        auto a = [1, 2, 3]
        auto b = a
        print(a)
    }
    '''
    try:
        check_ownership(src)
        assert False, "OwnershipError was expected"
    except OwnershipError:
        pass


def test_ownership_allows_use_before_move():
    src = '''
    fn main() {
        auto a = [1, 2, 3]
        print(a)
        auto b = a
        print(b)
    }
    '''
    assert check_ownership(src)


def test_ownership_rejects_double_free():
    src = '''
    fn main() {
        auto buffer = malloc(4)
        free(buffer)
        free(buffer)
    }
    '''
    try:
        check_ownership(src)
        assert False, "OwnershipError was expected"
    except OwnershipError:
        pass


def test_preprocessor_expands_defines_and_includes(tmp_path):
    header = tmp_path / "constants.autoc"
    header.write_text("auto offset = 2\n", encoding="utf-8")
    source = '#include "constants.autoc"\n#define WIDTH 3\nfn main() {\n    print(offset + WIDTH)\n}'
    expanded = preprocess(source, tmp_path)
    assert "auto offset = 2" in expanded
    assert "offset + 3" in expanded


def test_preprocessor_supports_function_macros_and_conditionals(tmp_path):
    header = tmp_path / "system.autoc"
    header.write_text("#define SCALE(x) ((x) * 2)\n", encoding="utf-8")
    source = '''
    #include <system.autoc>
    #define ENABLED 1
    #if ENABLED
    auto result = SCALE(3)
    #else
    auto result = 0
    #endif
    '''
    expanded = preprocess(source, tmp_path, include_paths=[tmp_path])
    assert "auto result = ((3) * 2)" in expanded
    assert "auto result = 0" not in expanded


def test_c_standard_library_equivalents():
    src = '''
    fn main() {
        auto text = "42"
        auto buffer = malloc(3)
        memset(buffer, 65, 3)
        print(strlen(text))
        print(atoi(text) + 1)
        puts("ok")
        free(buffer)
    }
    '''
    namespace = {}
    exec(compile_autoc_to_python(src), namespace, namespace)
    namespace["main"]()


def test_llvm_lowers_calls_and_control_flow():
    src = '''
    fn add(a: int, b: int) -> int {
        return a + b
    }
    fn main() -> void {
        auto value = add(1, 2)
        if value > 0 {
            value = value - 1
        }
        while value > 0 {
            value -= 1
        }
    }
    '''
    llvm = compile_autoc_to_llvm(src)
    assert llvm.count("define ") == 2
    assert "call i32 @add" in llvm
    assert "br i1" in llvm
    assert "while_body" in llvm


def test_native_target_compiler_selection(monkeypatch):
    monkeypatch.setattr("autoc.native.shutil.which", lambda name: "clang-path" if name == "clang" else None)
    assert find_compiler("linux-arm64") == "clang-path"
    assert normalize_target("linux-aarch64") == "linux-arm64"
    assert normalize_target("aarch64") == "linux-arm64"
    assert normalize_target("arm64") == "linux-arm64"
    assert normalize_target("amd64") == "linux-amd64"
    assert normalize_target("x86_64") == "linux-amd64"
    assert normalize_target("android-arm64-v8a") == "android-arm64"
    assert normalize_target("android-amd64") == "android-x86_64"
    assert normalize_target("arm32") == "linux-arm"
    assert normalize_target("x86") == "linux-i386"
    assert normalize_target("android-arm32") == "android-arm"
    assert normalize_target("android-x86") == "android-i386"


def test_c_frontend_parses_core_c_translation_unit():
    source = '''
    typedef struct Point { int x; int y; } Point;
    enum Color { RED, GREEN = 4, BLUE };
    int add(int left, int right) { return left + right; }
    int main(void) {
        Point point = {1, 2};
        int *value = &point.x;
        for (int index = 0; index < 2; index++) { point.x += index; }
        return add(*value, BLUE);
    }
    '''
    tree = parse_c(source, "compat.c")
    assert validate_c(source)
    assert len(tree.ext) == 4


def test_c_frontend_translates_executable_subset_to_python():
    source = '''
    int add(int left, int right) { return left + right; }
    int main(void) {
        int total = add(1, 2);
        for (int index = 0; index < 2; index++) { total += index; }
        return total;
    }
    '''
    generated = compile_c_to_python(source)
    namespace = {}
    exec(generated, namespace, namespace)
    assert namespace["main"]() == 4


def test_c_frontend_translates_printf_and_include_lines():
    source = '#include <stdio.h>\nint main(void) { printf("%d\\n", 7); return 0; }'
    generated = compile_c_to_python(source)
    namespace = {}
    exec(generated, namespace, namespace)
    assert namespace["main"]() == 0


def test_c_frontend_lowers_simple_function_to_llvm():
    source = "int add(int left, int right) { return left + right; }"
    llvm = compile_c_to_llvm(source)
    assert "define i32 @add" in llvm
    assert "add i32" in llvm


def test_llvm_emits_ir_for_function():
    src = '''
    fn add(a: int, b: int) -> int {
        auto total = a + b
        return total
    }
    '''
    llvm = compile_autoc_to_llvm(src)
    assert "define i32 @add" in llvm
    assert "ret i32" in llvm


def test_c_core_types_parse_and_lower_to_llvm():
    src = '''
    fn widen(value: double) -> double {
        return value
    }

    fn emit(letter: char) -> void {
        print(letter)
    }
    '''
    program = infer_types(src)
    assert program.items[0].params[0].type_name == "double"
    assert program.items[1].return_type == "void"
    assert "define double @widen" in compile_autoc_to_llvm(src)


def test_llvm_maps_c_core_types():
    from autoc.llvm_codegen import LLVMCodeGenerator

    generator = LLVMCodeGenerator()
    assert generator.map_type("char") == "i8"
    assert generator.map_type("double") == "double"
    assert generator.map_type("void") == "void"


def test_c_declarations_compound_assignments_and_operators():
    src = '''
    fn main() {
        int value = 1
        value += 3
        value = (value << 1) | 1
        print(value)
    }
    '''
    output = compile_autoc_to_python(src)
    assert "value = 1" in output
    assert "value = (value + 3)" in output
    assert "value = ((value << 1) | 1)" in output


def test_struct_union_enum_and_field_access():
    src = '''
    struct Point {
        int x;
        int y;
    }
    union Number {
        int integer;
        double decimal;
    }
    enum Color { RED, GREEN = 4, BLUE }

    fn main() {
        auto point = Point(2, 3)
        print(point.x + point.y)
        print(Color.BLUE)
    }
    '''
    output = compile_autoc_to_python(src)
    namespace = {}
    exec(output, namespace, namespace)
    assert namespace["Point"](2, 3).x == 2
    assert namespace["Color"].BLUE == 5


def test_safe_pointers_and_memory_helpers():
    src = '''
    fn main() {
        int value = 41
        auto pointer = &value
        print(*pointer + 1)
        auto buffer = malloc(4)
        free(buffer)
    }
    '''
    output = compile_autoc_to_python(src)
    namespace = {}
    exec(output, namespace, namespace)
    namespace["main"]()
