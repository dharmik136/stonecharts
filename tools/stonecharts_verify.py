#!/usr/bin/env python3
"""Compatibility wrapper for the packaged StoneVerify CLI."""

from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PY_LIB = ROOT / "libs" / "python"
sys.path.insert(0, str(PY_LIB))

from stonecharts.verify.cli import *  # noqa: F401,F403,E402
from stonecharts.verify.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
