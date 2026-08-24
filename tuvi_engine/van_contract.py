"""Canonical contract for the four authoritative Tử Vi vận layers.

The calculator may retain backward-compatible aliases, but AI-facing code must
consume only the canonical four layers defined here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

CANONICAL_LAYERS = (
    "dai_van",
    "luu_nien_dai_van",
    "tieu_van",
    "luu_nien_nam",
)

DEPRECATED_ALIASES = {
    "luu_nien_tieu_van": "luu_nien_nam",
    "luu_nien_tieu_van_10_nam": "luu_nien_nam_10_nam",
}


def _current(van: dict[str, Any], key: str, series_key: str, fallback: str | None = None) -> Any:
    value = van.get(key)
    if value is not None:
        return deepcopy(value)
    value = van.get(series_key)
    if isinstance(value, dict):
        return deepcopy(value)
    if isinstance(value, list):
        year = (van.get("year") or {}).get("nam")
        if year is not None:
            for row in value:
                if isinstance(row, dict) and row.get("nam") == year:
                    return deepcopy(row)
        if year is None:
            return deepcopy(value)
        return deepcopy(value[0]) if value else []
    if fallback:
        return deepcopy(van.get(fallback) or {})
    return {}


def canonicalize_van_layers(van: dict[str, Any] | None) -> dict[str, Any]:
    """Return a canonical current-year context plus explicit 10-year series.

    The current-year keys preserve the shape expected by existing API clients,
    while ``series`` carries the complete 10-year tables.
    """
    if not isinstance(van, dict):
        return {}

    out: dict[str, Any] = {
        "dai_van": _current(van, "dai_van", "dai_van_10_nam"),
        "luu_nien_dai_van": _current(van, "luu_nien_dai_van", "luu_nien_dai_van_10_nam", "luu_dai_van"),
        "tieu_van": _current(van, "tieu_van", "tieu_van_10_nam"),
        "luu_nien_nam": _current(van, "luu_nien_nam", "luu_nien_nam_10_nam", "luu_nien"),
        "series": {
            "dai_van": deepcopy(van.get("dai_van_10_nam") or []),
            "luu_nien_dai_van": deepcopy(van.get("luu_nien_dai_van_10_nam") or van.get("luu_nien_dai_van") or []),
            "tieu_van": deepcopy(van.get("tieu_van_10_nam") or []),
            "luu_nien_nam": deepcopy(van.get("luu_nien_nam_10_nam") or []),
        },
    }

    contract = deepcopy(van.get("sync_contract")) if isinstance(van.get("sync_contract"), dict) else {}
    out["sync_contract"] = contract
    out["source_of_truth"] = "FOUR_VAN_LAYERS"
    out["canonical_layers"] = list(CANONICAL_LAYERS)
    out["deprecated_aliases"] = dict(DEPRECATED_ALIASES)
    out["year"] = deepcopy(van.get("year") or {})
    return out


def validate_van_layer_contract(van: dict[str, Any] | None) -> list[str]:
    """Return contract violations instead of raising, for API/test diagnostics."""
    errors: list[str] = []
    if not isinstance(van, dict):
        return ["van phải là dict"]

    def first_present(*keys: str) -> Any:
        for key in keys:
            if key in van:
                return van[key]
        return None

    required = {
        "dai_van": first_present("dai_van_10_nam", "dai_van"),
        "luu_nien_dai_van": first_present("luu_nien_dai_van_10_nam", "luu_nien_dai_van", "luu_dai_van"),
        "tieu_van": first_present("tieu_van_10_nam", "tieu_van"),
        "luu_nien_nam": first_present("luu_nien_nam_10_nam", "luu_nien_nam", "luu_nien"),
    }
    for name, value in required.items():
        if value is None:
            errors.append(f"Thiếu lớp vận authoritative: {name}")

    sync = van.get("sync_contract") or {}
    if sync.get("source_of_truth") not in (None, "FOUR_VAN_LAYERS"):
        errors.append("sync_contract.source_of_truth không phải FOUR_VAN_LAYERS")

    if "luu_nien_tieu_van" in van and van.get("luu_nien_tieu_van") != van.get("luu_nien_nam"):
        errors.append("Alias luu_nien_tieu_van lệch khỏi luu_nien_nam")
    if "luu_nien_tieu_van_10_nam" in van and van.get("luu_nien_tieu_van_10_nam") != van.get("luu_nien_nam_10_nam"):
        errors.append("Alias luu_nien_tieu_van_10_nam lệch khỏi luu_nien_nam_10_nam")
    return errors


__all__ = ["CANONICAL_LAYERS", "DEPRECATED_ALIASES", "canonicalize_van_layers", "validate_van_layer_contract"]
