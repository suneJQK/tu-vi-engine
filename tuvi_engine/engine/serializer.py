"""Stable serialization helpers for low-level Tu Vi engine objects."""
from __future__ import annotations
from typing import Any, Iterable

from ..branch_names import branch_label, canonical_branch
from ..star_registry import (
    MAIN_STAR_IDS,
    TRANG_SINH_IDS,
    dedupe_stars as canonical_dedupe_stars,
    is_main_star,
    is_trang_sinh,
    normalize_star_record,
)

BRANCH_BOARD_POSITION = {
    "Tỵ": {"row": 1, "column": 1}, "Ngọ": {"row": 1, "column": 2},
    "Mùi": {"row": 1, "column": 3}, "Thân": {"row": 1, "column": 4},
    "Thìn": {"row": 2, "column": 1}, "Dậu": {"row": 2, "column": 4},
    "Mão": {"row": 3, "column": 1}, "Tuất": {"row": 3, "column": 4},
    "Dần": {"row": 4, "column": 1}, "Sửu": {"row": 4, "column": 2},
    "Tý": {"row": 4, "column": 3}, "Hợi": {"row": 4, "column": 4},
}


def serialize_star(star: Any) -> dict[str, Any]:
    """Convert any supported star object/dict into one stable JSON record."""
    normalized = normalize_star_record(star)
    return normalized or {
        "id": None, "ten": None, "ngu_hanh": None, "loai": None,
        "phuong_vi": None, "am_duong": None, "dac_tinh": None,
        "vong_trang_sinh": False,
    }


def dedupe_stars(stars: Iterable[Any]) -> list[dict[str, Any]]:
    return canonical_dedupe_stars(stars)


def serialize_palace(cung: Any, cung_so: int | None = None) -> dict[str, Any]:
    """Serialize palace identity, stars, and fixed physical board position."""
    stars = dedupe_stars(getattr(cung, "cungSao", []))
    main = [s for s in stars if is_main_star(s) or s.get("loai") == 1]
    trang_sinh = [s for s in stars if is_trang_sinh(s)]
    main_ids = {s.get("id") for s in main}
    trang_ids = {s.get("id") for s in trang_sinh}
    support = [s for s in stars if s.get("id") not in main_ids and s.get("id") not in trang_ids and not is_main_star(s)]
    raw_branch = getattr(cung, "cungDiaChi", "") or ""
    branch_key = canonical_branch(raw_branch, cung_so)
    branch = branch_label(raw_branch, cung_so) or raw_branch
    result = {
        "cung": getattr(cung, "cungChu", ""),
        "can_chi": getattr(cung, "cungTen", "").strip(),
        "dia_chi": branch,
        "branch": branch,
        "branch_key": branch_key,
        "ngu_hanh": getattr(cung, "cungHanh", getattr(cung, "hanhCung", "")),
        "am_duong": "Dương" if getattr(cung, "cungAmDuong", 0) == 1 else "Âm",
        "than_cu": bool(getattr(cung, "cungThan", False)),
        "tuan": bool(getattr(cung, "tuanTrung", False)),
        "triet": bool(getattr(cung, "trietLo", False)),
        "dai_van": {"tuoi_bat_dau": getattr(cung, "cungDaiHan", None)},
        "tieu_van": {"chi": getattr(cung, "cungTieuHan", None)},
        "chinh_tinh": main,
        "phu_tinh": support,
        "vong_trang_sinh": next((s["ten"] for s in trang_sinh), None),
        "sao": stars,
    }
    position = BRANCH_BOARD_POSITION.get(branch)
    if position:
        result["vi_tri"] = position
    if cung_so is not None:
        result["cung_so"] = int(cung_so)
    return result


__all__ = ["MAIN_STAR_IDS", "TRANG_SINH_IDS", "serialize_star", "dedupe_stars", "serialize_palace"]
