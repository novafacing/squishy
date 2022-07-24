"""
Build script to install squishy as a python library
"""
from mesonbuild.mesonmain import run
from shutil import which, copyfile
from pathlib import Path
from os import chdir

SQUISHY_DIR = Path(__file__).parent
SQUISHY_BUILDDIR = SQUISHY_DIR / "build"
SQUISHY_BUILD_LIB = SQUISHY_BUILDDIR / "src" / "libsquishy.so"
SQUISHY_LIBDIR = SQUISHY_DIR / "squishy" / "lib"
SQUISHY_LIB = SQUISHY_LIBDIR / "libsquishy.so"


def build(_) -> None:
    """
    Build squishy passes and install a wrapper for it as a Python library
    """
    chdir(SQUISHY_DIR)
    run(["build"], which("meson"))

    if not SQUISHY_BUILDDIR.is_dir():
        raise Exception(f"Build directory {SQUISHY_BUILDDIR} not created.")

    chdir(SQUISHY_BUILDDIR)
    run(["compile"], which("meson"))

    if not SQUISHY_BUILD_LIB.is_file():
        raise Exception(f"Squishy library {SQUISHY_BUILD_LIB} not created.")

    copyfile(SQUISHY_BUILD_LIB, SQUISHY_LIB)
