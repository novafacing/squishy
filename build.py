"""
Build script to install squishy as a python library
"""
from pathlib import Path
from shutil import copyfile
from subprocess import run, CalledProcessError

SQUISHY_DIR = Path(__file__).parent
SQUISHY_BUILDDIR = SQUISHY_DIR / "builddir"
SQUISHY_BUILD_LIB = SQUISHY_BUILDDIR / "src" / "libsquishy.so"
SQUISHY_LIBDIR = SQUISHY_DIR / "squishy" / "lib"
SQUISHY_LIB = SQUISHY_LIBDIR / "libsquishy.so"


def build(_) -> None:
    """
    Build squishy passes and install a wrapper for it as a Python library
    """
    if not SQUISHY_BUILDDIR.is_dir():
        try:
            run(["meson", "builddir"], cwd=SQUISHY_DIR, check=True, capture_output=True)
        except CalledProcessError as e:
            raise Exception("Failed to build squishy passes") from e

    if not SQUISHY_BUILDDIR.is_dir():
        raise Exception(f"Build directory {SQUISHY_BUILDDIR} not created.")

    if not SQUISHY_BUILD_LIB.is_file():
        try:
            run(
                ["meson", "compile"],
                cwd=SQUISHY_BUILDDIR,
                check=True,
                capture_output=True,
            )
        except CalledProcessError as e:
            raise Exception("Failed to build squishy passes") from e

    if not SQUISHY_BUILD_LIB.is_file():
        raise Exception(f"Squishy library {SQUISHY_BUILD_LIB} not created.")

    try:
        copyfile(SQUISHY_BUILD_LIB, SQUISHY_LIB)
    except Exception as e:
        raise Exception("Failed to copy squishy library") from e
