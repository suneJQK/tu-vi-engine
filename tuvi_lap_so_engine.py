"""Backward-compatible entry point for the local Tu Vi chart engine.

The implementation now lives in ``tuvi_engine.engine``. This module keeps the
legacy ``lap_la_so(...)`` import working for the existing Streamlit application
and external callers.
"""
from __future__ import annotations

from typing import Any

from tuvi_engine.engine.chart_builder import lap_la_so
from tuvi_engine.engine.date_handler import (
    BRANCH_TO_INDEX,
    parse_gender as _gender_value,
    parse_hour_branch as _hour_branch,
)
from tuvi_engine.engine.serializer import (
    MAIN_STAR_IDS,
    TRANG_SINH_IDS,
    dedupe_stars as _dedupe,
    serialize_palace as _palace_json,
    serialize_star as _star_dict,
)

__all__ = [
    "lap_la_so",
    "BRANCH_TO_INDEX",
    "MAIN_STAR_IDS",
    "TRANG_SINH_IDS",
    "_gender_value",
    "_hour_branch",
    "_star_dict",
    "_dedupe",
    "_palace_json",
]
