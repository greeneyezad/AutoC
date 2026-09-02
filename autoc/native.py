import os
import shutil
import subprocess
import tempfile
from pathlib import Path

class NativeBuildError(RuntimeError):
    pass


TARGET_ALIASES = {
    "linux-aarch64": "linux-arm64",
    "aarch64": "linux-arm64",
    "arm64": "linux-arm64",
    "linux-x86_64": "linux-amd64",
    "amd64": "linux-amd64",
    "x86_64": "linux-amd64",
    "android-arm64-v8a": "android-arm64",
    "android-amd64": "android-x86_64",
    "linux-arm32": "linux-arm",
    "arm32": "linux-arm",
    "linux-x86": "linux-i386",
    "x86": "linux-i386",
    "android-arm32": "android-arm",
    "android-x86": "android-i386",
}


def normalize_target(target):
    return TARGET_ALIASES.get(target, target)


def find_compiler(target, compiler=None):
    target = normalize_target(target)
    if compiler:
        return compiler
    if target in {"linux-arm64", "linux-amd64", "linux-arm", "linux-i386"}:
        return shutil.which("clang")
    if target in {"android-arm64", "android-x86_64", "android-arm", "android-i386"}:
        ndk = os.environ.get("ANDROID_NDK_HOME")
        if ndk:
            tool_dir = Path(ndk) / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin"
            prefixes = {
                "android-arm64": "aarch64-linux-android",
                "android-x86_64": "x86_64-linux-android",
                "android-arm": "armv7a-linux-androideabi",
                "android-i386": "i686-linux-android",
            }
            for suffix in (".cmd", ""):
                candidate = tool_dir / (prefixes[target] + "24-clang" + suffix)
                if candidate.is_file():
                    return str(candidate)
        prefixes = {
            "android-arm64": "aarch64-linux-android",
            "android-x86_64": "x86_64-linux-android",
            "android-arm": "armv7a-linux-androideabi",
            "android-i386": "i686-linux-android",
        }
        return shutil.which("%s24-clang" % prefixes[target])
    raise NativeBuildError("Unsupported native target: %s" % target)


def build_native(source, output, target="linux-arm64", compiler=None, kind="shared"):
    target = normalize_target(target)
    from .interpreter import compile_autoc_to_llvm

    compiler_path = find_compiler(target, compiler)
    if compiler_path is None:
        hint = "Install LLVM/Clang for Linux AArch64 or AMD64"
        if target in {"android-arm64", "android-x86_64"}:
            hint = "Install the Android NDK and set ANDROID_NDK_HOME"
        raise NativeBuildError("No compiler found for %s. %s." % (target, hint))

    llvm = compile_autoc_to_llvm(source)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ll", encoding="utf-8", delete=False) as ir_file:
        ir_file.write(llvm)
        ir_path = ir_file.name

    command = [compiler_path]
    linux_targets = {
        "linux-arm64": "aarch64-linux-gnu",
        "linux-amd64": "x86_64-linux-gnu",
        "linux-arm": "arm-linux-gnueabihf",
        "linux-i386": "i386-linux-gnu",
    }
    if target in linux_targets:
        command.append("--target=" + linux_targets[target])
    if kind == "shared":
        command.extend(["-shared", "-fPIC"])
    elif kind != "executable":
        raise NativeBuildError("Unsupported native output kind: %s" % kind)
    command.extend(["-x", "ir", ir_path, "-o", str(output)])
    try:
        subprocess.run(command, check=True)
    except OSError as error:
        raise NativeBuildError("Could not execute native compiler: %s" % error) from error
    except subprocess.CalledProcessError as error:
        raise NativeBuildError("Native compiler failed with exit code %d" % error.returncode) from error
    finally:
        Path(ir_path).unlink(missing_ok=True)
    return output