# Native Builds

AutoC is implemented in Python and compiles its supported C-like language to
LLVM IR. Clang then produces native shared libraries for AArch64 targets.

## Linux AArch64

Install LLVM/Clang and run:

```text
python -m autoc examples/compat/sum.autoc --emit-native --target linux-aarch64 -o libsum.so
```

`linux-aarch64` and `linux-arm64` are equivalent target names.

Linux AMD64 builds use:

```text
python -m autoc examples/compat/sum.autoc --emit-native --target amd64 -o libsum.so
```

`amd64`, `x86_64`, and `linux-amd64` are equivalent target names.

## Android arm64-v8a

Install the Android NDK, set `ANDROID_NDK_HOME`, and run:

```text
python -m autoc examples/compat/sum.autoc --emit-native --target android-arm64-v8a -o libsum.so
```

`android-arm64-v8a` and `android-arm64` are equivalent target names.

For Android x86_64 use `--target android-amd64`. The Android NDK compiler is
selected automatically for either ABI.

The `.c` file beside the example is a reference implementation used for
compatibility review. AutoC does not yet accept arbitrary legacy C source; it
accepts the documented AutoC syntax and emits native code from that syntax.