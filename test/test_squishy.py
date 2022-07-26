"""
Tests for squishy
"""

from pathlib import Path
from pysquishy.squishy import Squishy

CHECK_C_FILE = Path(__file__).with_name("check.c")


def test_basic() -> None:
    """
    Test a basic full squishy run
    """
    squishy = Squishy()
    main_func = squishy.compile(CHECK_C_FILE)
    print(main_func)
