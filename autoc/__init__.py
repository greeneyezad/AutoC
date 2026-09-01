"""AutoC package."""

from .interpreter import compile_autoc_to_python, run_autoc_string, run_autoc_file

__all__ = ["compile_autoc_to_python", "run_autoc_string", "run_autoc_file"]
