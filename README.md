# squishy 🐻‍❄️

A collection of new (LLVM 15) passes to compile normal-looking code to a callable, jump-to-able blob.

Inspired by SheLLVM, but should address some of the outdated issues with
that project. Thanks to SheLLVM for the inspiration :)

## Building

`squishy 🐻‍❄️` uses the [meson](https://mesonbuild.com) modern build system. To
build, first ensure that `meson` and `ninja` are installed, and that you have
an installation of `llvm-15` which you can get [here](https://apt.llvm.com).

Then, invoke:

```
meson build
cd build
meson compile
```

to produce the [library](build/src/libsquishy.so).


## Passes

1. Aggressive Inliner: Recursively applies alwaysinline and inlines function
  calls.
2. Deduplicate Calls: Repeated calls to inlined code can be directed to
   a block in the main function as if it were a function without making
   a call.
3. Inline Globals: Global variables need to be inlined wherever they are
   used (in practice, stack all globals into the main function).