import os
import shutil
import subprocess
import tempfile
from pathlib import Path

class NativeBuildError(RuntimeError):
    pass


TARGET_ALIASES = {
    "linux-aarch64": "linux-arm64",
    "android-arm64-v8a": "android-arm64",
}


def normalize_target(target):
    return TARGET_ALIASES.get(target, target)


def find_compiler(target, compiler=None):
    target = normalize_target(target)
    if compiler:
        return compiler
    if target == "linux-arm64":
        return shutil.which("clang")
    if target == "android-arm64":
        ndk = os.environ.get("ANDROID_NDK_HOME")
        if ndk:
            tool_dir = Path(ndk) / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin"
            candidate = tool_dir / "aarch64-linux-android24-clang.cmd"
            if candidate.is_file():
                return str(candidate)
            candidate = tool_dir / "aarch64-linux-android24-clang"
            if candidate.is_file():
                return str(candidate)
        return shutil.which("aarch64-linux-android24-clang")
    raise NativeBuildError("Unsupported native target: %s" % target)


def build_native(source, output, target="linux-arm64", compiler=None):
    target = normalize_target(target)
    from .interpreter import compile_autoc_to_llvm

    compiler_path = find_compiler(target, compiler)
    if compiler_path is None:
        hint = "Install LLVM/Clang for Linux AArch64"
        if target == "android-arm64":
            hint = "Install the Android NDK and set ANDROID_NDK_HOME"
        raise NativeBuildError("No compiler found for %s. %s." % (target, hint))

    llvm = compile_autoc_to_llvm(source)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ll", encoding="utf-8", delete=False) as ir_file:
        ir_file.write(llvm)
        ir_path = ir_file.name

    command = [compiler_path]
    if target == "linux-arm64":
        command.append("--target=aarch64-linux-gnu")
    command.extend(["-shared", "-fPIC", "-x", "ir", ir_path, "-o", str(output)])
    try:
        subprocess.run(command, check=True)
    except OSError as error:
        raise NativeBuildError("Could not execute native compiler: %s" % error) from error
    except subprocess.CalledProcessError as error:
        raise NativeBuildError("Native compiler failed with exit code %d" % error.returncode) from error
    finally:
        Path(ir_path).unlink(missing_ok=True)
    return output