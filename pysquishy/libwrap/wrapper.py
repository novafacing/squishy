"""
Wrapper exports for squishy library
"""

from pathlib import Path

LIBSQUISHY_DIR = Path(__file__).parent
LIBSQUISHY_LIB = LIBSQUISHY_DIR / "libsquishy.so"

if not LIBSQUISHY_LIB.is_file():
    raise FileNotFoundError(f"Squishy library {LIBSQUISHY_LIB} not found.")
