import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from autoc.interpreter import compile_autoc_to_python, run_autoc_string, compile_autoc_to_llvm
from autoc.type_inference import infer_types, TypeInferenceError
from autoc.ownership import OwnershipError, check_ownership


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
