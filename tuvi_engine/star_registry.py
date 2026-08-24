"""Canonical star lookup/normalization API for the local Tử Vi engine.

The low-level ``Sao.py`` objects remain the source of truth. All higher layers
should resolve a star through this module instead of comparing ad-hoc fields.
"""
from __future__ import annotations

import importlib
import unicodedata
from functools import lru_cache
from typing import Any, Iterable

MAIN_STAR_IDS = frozenset(range(1, 15))
TRANG_SINH_IDS = frozenset(range(39, 51))
TRANSFORMATION_IDS = frozenset(range(92, 96))


def normalize_star_name(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "").strip().casefold())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


@lru_cache(maxsize=1)
def _engine_stars() -> dict[int, Any]:
    sao_module = importlib.import_module(". _engine.Sao".replace(" ", ""), package="tuvi_engine")
    sao_type = getattr(sao_module, "Sao")
    result: dict[int, Any] = {}
    for value in vars(sao_module).values():
        if isinstance(value, sao_type):
            try:
                sid = int(value.saoID)
            except (TypeError, ValueError):
                continue
            result[sid] = value
    return result


@lru_cache(maxsize=1)
def _registry_by_name() -> dict[str, int]:
    return {
        normalize_star_name(star.saoTen): sid
        for sid, star in _engine_stars().items()
        if getattr(star, "saoTen", None)
    }


def star_id(value: Any) -> int | None:
    """Resolve a star from numeric ID or any supported name representation."""
    if isinstance(value, bool):
        return None
    try:
        if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
            sid = int(value)
            return sid if sid in _engine_stars() else None
    except (TypeError, ValueError):
        pass

    if isinstance(value, dict):
        for key in ("id", "saoID"):
            resolved = star_id(value.get(key))
            if resolved is not None:
                return resolved
        value = value.get("ten") or value.get("name") or value.get("saoTen") or value.get("sao")

    return _registry_by_name().get(normalize_star_name(value))


def canonical_star_name(value: Any) -> str | None:
    sid = star_id(value)
    if sid is None:
        text = str(value or "").strip()
        return text or None
    star = _engine_stars().get(sid)
    return str(getattr(star, "saoTen", "") or "").strip() or None


def normalize_star_record(raw: Any) -> dict[str, Any] | None:
    """Convert any supported star representation to one stable dictionary."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        item = dict(raw)
        sid = star_id(item)
        name = canonical_star_name(sid) if sid is not None else (item.get("ten") or item.get("name") or item.get("saoTen") or item.get("sao"))
        if not name:
            return None
        item["id"] = sid if sid is not None else item.get("id", item.get("saoID"))
        item["ten"] = name
        if item.get("loai") is None:
            item["loai"] = item.get("saoLoai")
        if item.get("vong_trang_sinh") is None:
            item["vong_trang_sinh"] = bool(item.get("vongTrangSinh"))
        return item

    sid = star_id(raw)
    if sid is None:
        return None
    star = _engine_stars()[sid]
    return {
        "id": sid,
        "ten": str(getattr(star, "saoTen", "") or "").strip(),
        "ngu_hanh": getattr(star, "saoNguHanh", None),
        "loai": getattr(star, "saoLoai", None),
        "phuong_vi": getattr(star, "saoPhuongVi", None),
        "am_duong": getattr(star, "saoAmDuong", None),
        "dac_tinh": getattr(star, "saoDacTinh", None),
        "vong_trang_sinh": bool(getattr(star, "vongTrangSinh", False)),
    }


def dedupe_stars(stars: Iterable[Any] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[int | str] = set()
    for raw in stars or []:
        star = normalize_star_record(raw)
        if not star:
            continue
        sid = star.get("id")
        key: int | str = sid if sid is not None else normalize_star_name(star.get("ten"))
        if key in seen:
            continue
        seen.add(key)
        out.append(star)
    return out


def has_star(palace_or_stars: Any, star: Any, star_attr: str | None = None) -> bool:
    wanted_id = star_id(star)
    wanted_name = normalize_star_name(star) if wanted_id is None else None
    records = palace_or_stars if isinstance(palace_or_stars, list) else (
        [] if not isinstance(palace_or_stars, dict) else (
            (palace_or_stars.get("sao") or [])
            + (palace_or_stars.get("chinh_tinh") or [])
            + (palace_or_stars.get("phu_tinh") or [])
        )
    )
    for raw in dedupe_stars(records):
        rid = star_id(raw)
        if wanted_id is not None and rid != wanted_id:
            continue
        if wanted_id is None and normalize_star_name(raw.get("ten")) != wanted_name:
            continue
        if star_attr is not None:
            actual = normalize_star_name(raw.get("dac_tinh") or raw.get("attribute") or raw.get("saoDacTinh"))
            if normalize_star_name(star_attr) not in actual:
                continue
        return True
    return False


def stars_in(palace_or_stars: Any) -> list[dict[str, Any]]:
    if isinstance(palace_or_stars, dict):
        records = ((palace_or_stars.get("sao") or []) + (palace_or_stars.get("chinh_tinh") or []) + (palace_or_stars.get("phu_tinh") or []))
    else:
        records = palace_or_stars or []
    return dedupe_stars(records)


def is_main_star(value: Any) -> bool:
    sid = star_id(value)
    return sid in MAIN_STAR_IDS if sid is not None else False


def is_trang_sinh(value: Any) -> bool:
    sid = star_id(value)
    if sid in TRANG_SINH_IDS:
        return True
    normalized = normalize_star_record(value)
    return bool(normalized and normalized.get("vong_trang_sinh"))


def is_transformation(value: Any) -> bool:
    sid = star_id(value)
    return sid in TRANSFORMATION_IDS if sid is not None else False


def star_catalog() -> list[dict[str, Any]]:
    """Return every star known to the low-level engine, resolved by ID."""
    records = (normalize_star_record(sid) for sid in sorted(_engine_stars()))
    return [record for record in records if record]


__all__ = [
    "MAIN_STAR_IDS", "TRANG_SINH_IDS", "TRANSFORMATION_IDS",
    "normalize_star_name", "star_id", "canonical_star_name",
    "normalize_star_record", "dedupe_stars", "has_star", "stars_in",
    "is_main_star", "is_trang_sinh", "is_transformation", "star_catalog",
]
