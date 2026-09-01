import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from autoc.interpreter import run_autoc_string


def benchmark_python_sum(limit=200000):
    code = f'''
    fn main() {{
        auto total = 0
        for auto i in range({limit}) {{
            total = total + i
        }}
        print(total)
    }}
    '''
    start = time.perf_counter()
    run_autoc_string(code)
    end = time.perf_counter()
    return end - start


if __name__ == "__main__":
    elapsed = benchmark_python_sum()
    print(f"AutoC benchmark: {elapsed:.6f}s")
