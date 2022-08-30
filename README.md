# squishy 🐻‍❄️

A collection of new (LLVM 15) passes to compile normal-looking code to a callable, jump-to-able blob. Also includes a python library that provides
a python interface to produce a blob for any architecture triple.

Inspired by SheLLVM, but should address some of the outdated issues with
that project. Thanks to SheLLVM for the inspiration :)

## Installing

### Dependencies

* LLVM-15: Install with `wget -qO - https://apt.llvm.org/llvm.sh | sudo bash -s 15`
* Meson 0.63+: Install with `pip install -U meson` and add `~/.local` to your path

To set up LLVM-15 as alternatives you can run [scripts/set-alternatives.sh](scripts/set-alternatives.sh)

The easiest way to install `squishy 🐻‍❄️` is from PyPi (sorry about the name, PyPi has weird rules). If an sdist is installed, `meson` must be installed and
`llvm-15` must be available.

```
python3 -m pip install pysquishy>=0.1.16
```

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
  calls and global variables into the main function.