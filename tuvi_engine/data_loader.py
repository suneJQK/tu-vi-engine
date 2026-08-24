"""Load V2 data catalogs without coupling callers to repository paths."""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=32)
def _read_json(relative_path: str) -> Any:
    with (ROOT / relative_path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_json(relative_path: str) -> Any:
    """Cached read. Callers must not mutate the returned object in place."""
    return _read_json(relative_path)


def load_star_registry() -> dict[str, Any]:
    return load_json("data/stars.json")


def load_engine_config() -> dict[str, Any]:
    return load_json("data/tu_vi_engine.json")


@lru_cache(maxsize=1)
def _cach_cuc_merged() -> list[dict[str, Any]]:
    data = load_json("data/cach_cuc.json")
    if not isinstance(data, list):
        return []

    # Keep the rich source file intact while allowing verified rule corrections
    # to be versioned separately and applied deterministically at runtime.
    overrides = load_json("data/cach_cuc_overrides.json")
    if isinstance(overrides, dict):
        merged: list[dict[str, Any]] = []
        for item in data:
            current = dict(item)
            replacement = overrides.get(str(item.get("id")))
            if isinstance(replacement, dict):
                current["conditions"] = replacement
            merged.append(current)
        return merged

    return data


def load_cach_cuc() -> list[dict[str, Any]]:
    return _cach_cuc_merged()
