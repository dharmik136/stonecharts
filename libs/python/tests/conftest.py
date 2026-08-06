"""Make the `stonecharts` package importable for every test module in this directory.

pytest collects test files in a single process, so whichever module runs first and
inserts `libs/python` onto `sys.path` leaves that path change in effect for every
module collected afterward. That made `test_stonecharts_verify.py` and
`test_verify_result.py` pass only when collected after `test_golden.py` (which
already did this insert) and fail when run in isolation. conftest.py runs once per
test session regardless of collection order, so every module in this directory can
rely on `stonecharts` being importable without needing its own sys.path setup.

Mirrors the sys.path setup in test_golden.py.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs" / "python"))
