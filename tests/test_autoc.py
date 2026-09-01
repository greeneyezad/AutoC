import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from autoc.interpreter import compile_autoc_to_python, run_autoc_string


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
