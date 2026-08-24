"""Canonical địa chi helpers shared by the chart normalizer and UI contract."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CATALOG = json.loads((Path(__file__).resolve().parent.parent / "data" / "branch_aliases.json").read_text(encoding="utf-8"))
BRANCH_ORDER = tuple(_CATALOG["order"])
BRANCH_LABELS = {key: value["label"] for key, value in _CATALOG["branches"].items()}
BRANCH_ALIASES = {alias.casefold(): key for key, value in _CATALOG["branches"].items() for alias in value["aliases"]}


def canonical_branch(value: Any, cung_so: Any = None) -> str | None:
    """Return the single canonical branch key, e.g. ``ty`` or ``ti``."""
    if value is not None:
        key = BRANCH_ALIASES.get(str(value).strip().casefold())
        if key:
            return key
    try:
        index = int(cung_so)
        if 1 <= index <= 12:
            return BRANCH_ORDER[index - 1]
    except (TypeError, ValueError):
        pass
    return None


def branch_label(value: Any, cung_so: Any = None) -> str | None:
    key = canonical_branch(value, cung_so)
    return BRANCH_LABELS.get(key) if key else None
