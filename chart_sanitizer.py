# -*- coding: utf-8 -*-
"""Chuẩn hóa dữ liệu sao của engine trước khi hiển thị hoặc gửi AI."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from tuvi_engine.branch_names import BRANCH_LABELS, canonical_branch
from tuvi_engine.star_registry import (
    MAIN_STAR_IDS,
    TRANG_SINH_IDS,
    TRANSFORMATION_IDS,
    canonical_star_name,
    dedupe_stars,
    is_main_star,
    is_trang_sinh,
    normalize_star_name,
)

BRANCHES = [BRANCH_LABELS[key] for key in ("ty", "suu", "dan", "mao", "thin", "ti", "ngo", "mui", "than", "dau", "tuat", "hoi")]
MAIN_STAR_NAMES = frozenset(canonical_star_name(i) for i in MAIN_STAR_IDS if canonical_star_name(i))


def _normalize_star(raw: Any) -> dict[str, Any] | None:
    """Backward-compatible alias to the canonical registry normalizer."""
    from tuvi_engine.star_registry import normalize_star_record
    return normalize_star_record(raw)


def _key(star: dict[str, Any]) -> tuple[str, Any]:
    sid = star.get("id")
    return ("id", str(sid)) if sid is not None else ("name", normalize_star_name(star.get("ten")))


def _star_name(star: dict[str, Any]) -> str:
    return normalize_star_name(star.get("ten"))


def split_engine_stars(stars: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Trả về (chính tinh, phụ tinh, vòng Tràng Sinh) qua một registry duy nhất."""
    main: list[dict[str, Any]] = []
    support: list[dict[str, Any]] = []
    trang_sinh: list[dict[str, Any]] = []
    for star in dedupe_stars(stars):
        if is_main_star(star): main.append(star)
        elif is_trang_sinh(star): trang_sinh.append(star)
        else: support.append(star)
    return main, support, trang_sinh


def _canonical_branch(value: Any, cung_so: Any = None) -> str | None:
    key = canonical_branch(value, cung_so)
    return BRANCH_LABELS.get(key) if key else None


def _list_alias(raw: dict[str, Any], *keys: str) -> list[Any]:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list) and value: return value
    return []


def normalize_engine_chart(chart: Any, *, for_ai: bool = False) -> dict[str, Any]:
    """Chuẩn hóa chart; mỗi cung giữ đủ chính tinh, phụ tinh và Tràng Sinh."""
    if not isinstance(chart, dict): return {}
    out = dict(chart)
    cungs = chart.get("12_cung", {})
    normalized: dict[str, Any] = {}
    iterable = cungs.items() if isinstance(cungs, dict) else enumerate(cungs, 1)
    for name, raw in iterable:
        if not isinstance(raw, dict): continue
        item = dict(raw)
        item["cung"] = str(raw.get("cung") or raw.get("ten_cung") or name)
        raw_branch = raw.get("dia_chi") or raw.get("chi") or raw.get("branch")
        item["dia_chi_raw"] = raw_branch
        item["branch_key"] = canonical_branch(raw_branch, raw.get("cung_so"))
        item["branch"] = _canonical_branch(raw_branch, raw.get("cung_so"))
        item["dia_chi"] = item["branch"] or raw_branch
        explicit_main = _list_alias(raw, "chinh_tinh", "chinhTinh", "chinhTinhData")
        explicit_support = _list_alias(raw, "phu_tinh", "phuTinh", "phuTinhData")
        explicit_trang = _list_alias(raw, "vong_trang_sinh_data", "vongTrangSinhData")
        raw_all = _list_alias(raw, "sao", "stars", "all_stars")
        if explicit_main or explicit_support or explicit_trang:
            main = dedupe_stars(explicit_main)
            support = dedupe_stars(explicit_support)
            trang_sinh = dedupe_stars(explicit_trang)
            if raw_all:
                raw_main, raw_support, raw_trang = split_engine_stars(raw_all)
                if not main: main = raw_main
                if not support: support = raw_support
                if not trang_sinh: trang_sinh = raw_trang
        else:
            main, support, trang_sinh = split_engine_stars(raw_all)
        item["chinh_tinh"] = main
        item["phu_tinh"] = support
        item["vong_trang_sinh_data"] = trang_sinh
        item["trang_sinh"] = next((x.get("ten") for x in trang_sinh if x.get("ten")), item.get("vong_trang_sinh"))
        item["vong_trang_sinh"] = item["trang_sinh"]
        item["tuan_triet"] = ", ".join(x for x, ok in (("Tuần", raw.get("tuan")), ("Triệt", raw.get("triet"))) if ok) or None
        if for_ai:
            item.pop("sao", None); item.pop("stars", None); item.pop("tuan", None); item.pop("triet", None); item.pop("vong_trang_sinh_data", None)
        normalized[str(name)] = item
    out["12_cung"] = normalized
    return out
