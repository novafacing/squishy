"""
Build script to install squishy as a python library
"""
from pathlib import Path
from shutil import copyfile
from subprocess import run, CalledProcessError

SQUISHY_DIR = Path(__file__).parent
SQUISHY_BUILDDIR = SQUISHY_DIR / "builddir"
SQUISHY_BUILT_SRC = SQUISHY_BUILDDIR / "src"
SQUISHY_BUILD_LIB = SQUISHY_BUILT_SRC / "libsquishy.so"
SQUISHY_LIBDIR = SQUISHY_DIR / "pysquishy" / "libwrap"
SQUISHY_LIB = SQUISHY_LIBDIR / "libsquishy.so"


def build(_) -> None:
    """
    Build squishy passes and install a wrapper for it as a Python library
    """
    if not SQUISHY_BUILDDIR.is_dir():
        try:
            run(
                ["meson", "builddir"],
                cwd=SQUISHY_DIR.resolve(),
                check=True,
                capture_output=True,
            )
        except CalledProcessError as e:
            raise Exception(
                f"Failed to build squishy passes:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            ) from e

    if not SQUISHY_BUILDDIR.is_dir():
        raise Exception(f"Build directory {SQUISHY_BUILDDIR} not created.")

    if not SQUISHY_BUILD_LIB.is_file():
        try:
            run(
                ["meson", "compile"],  # , "--buildtype=debug"],
                cwd=SQUISHY_BUILDDIR.resolve(),
                check=True,
                capture_output=True,
            )
        except CalledProcessError as e:
            raise Exception(
                f"Failed to build squishy passes:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            ) from e

    if not SQUISHY_BUILD_LIB.is_file():
        raise Exception(f"Squishy library {SQUISHY_BUILD_LIB} not created.")

    try:
        copyfile(SQUISHY_BUILD_LIB.resolve(), SQUISHY_LIB.resolve())
    except Exception as e:
        dirlisting = "\n".join(list(map(str, SQUISHY_BUILT_SRC.iterdir())))
        raise Exception(f"Failed to copy squishy library:\n{dirlisting}") from e
