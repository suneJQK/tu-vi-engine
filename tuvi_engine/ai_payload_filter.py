"""Deterministic pre-AI payload filter.

This module does not interpret astrology. It selects the minimum evidence set
needed for AI reasoning while preserving every natal star in selected palaces
and all authoritative four-layer vận data.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .data_loader import load_json

DYNAMIC_FIELDS = {
    "dai_van", "tieu_van", "luu_nien", "luu_dai_van", "luu_nguyet",
    "luu_nhat", "luu_thoi"
}
BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
TAM_HOP = [frozenset(x) for x in (("Thân", "Tý", "Thìn"), ("Dần", "Ngọ", "Tuất"), ("Tỵ", "Dậu", "Sửu"), ("Hợi", "Mão", "Mùi"))]
NHI_HOP = {"Tý":"Sửu","Sửu":"Tý","Dần":"Hợi","Hợi":"Dần","Mão":"Tuất","Tuất":"Mão","Thìn":"Dậu","Dậu":"Thìn","Tỵ":"Thân","Thân":"Tỵ","Ngọ":"Mùi","Mùi":"Ngọ"}
_RELATION_DATA = load_json("data/relationships_ai.json")


def _norm_branch(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().casefold()
    aliases = {
        "ty1":"Tý", "ty":"Tý", "tý":"Tý", "ty2":"Tỵ", "tỵ":"Tỵ", "tị":"Tỵ",
        "suu":"Sửu", "dan":"Dần", "mao":"Mão", "thin":"Thìn", "ngo":"Ngọ",
        "mui":"Mùi", "than":"Thân", "dau":"Dậu", "tuat":"Tuất", "hoi":"Hợi",
    }
    return aliases.get(raw)


def _strip_dynamic(palace: dict[str, Any]) -> dict[str, Any]:
    item = deepcopy(palace)
    for key in DYNAMIC_FIELDS:
        item.pop(key, None)
    return item


def _palaces(chart: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for raw in (chart.get("12_cung") or {}).values():
        if not isinstance(raw, dict):
            continue
        try:
            n = int(raw.get("cung_so"))
        except (TypeError, ValueError):
            continue
        out[n] = _strip_dynamic(raw)
    return out


def _positions_from_rows(rows: Any, year: int | None) -> set[int]:
    positions: set[int] = set()
    if not isinstance(rows, list):
        return positions
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            positions.add(int(row["cung_so"]))
        except (TypeError, ValueError, KeyError):
            continue
        if year is not None and row.get("nam") == year:
            try:
                positions.add(int(row["cung_so"]))
            except (TypeError, ValueError):
                pass
    return positions


def _four_layer_positions(van: dict[str, Any], year: int | None) -> dict[str, set[int]]:
    dv = van.get("dai_van") or {}
    dv_cur = dv.get("dang_xet") or {}
    dai = set()
    try:
        dai.add(int(dv_cur.get("cung_so")))
    except (TypeError, ValueError):
        pass
    luu_dv = _positions_from_rows(van.get("luu_nien_dai_van_10_nam"), year)
    tieu = _positions_from_rows(van.get("tieu_van_10_nam"), year)
    luu_nam = _positions_from_rows(van.get("luu_nien_nam_10_nam") or van.get("luu_nien_tieu_van_10_nam"), year)
    return {"dai_van": dai, "luu_nien_dai_van": luu_dv, "tieu_van": tieu, "luu_nien_nam": luu_nam}


def _expand_relations(palaces: dict[int, dict[str, Any]], seeds: set[int]) -> tuple[set[int], list[dict[str, Any]]]:
    selected = set(seeds)
    relations: list[dict[str, Any]] = []
    by_branch = { _norm_branch(v.get("dia_chi")): n for n, v in palaces.items() }
    for n in list(seeds):
        p = palaces.get(n)
        if not p:
            continue
        branch = _norm_branch(p.get("dia_chi"))
        for rel, target in (("xung_chieu", (n + 6 - 1) % 12 + 1), ("giap_cung", (n - 2) % 12 + 1), ("giap_cung", n % 12 + 1)):
            if target in palaces:
                selected.add(target)
                relations.append({"from": n, "to": target, "quan_he": rel})
        if branch in NHI_HOP and NHI_HOP[branch] in by_branch:
            target = by_branch[NHI_HOP[branch]]
            selected.add(target)
            relations.append({"from": n, "to": target, "quan_he": "nhi_hop"})
        for group in TAM_HOP:
            if branch in group:
                for b, target in by_branch.items():
                    if b in group and target != n:
                        selected.add(target)
                        relations.append({"from": n, "to": target, "quan_he": "tam_hop"})
                break
    return selected, relations


def _domain_seeds(question: str, palaces: dict[int, dict[str, Any]]) -> set[int]:
    q = (question or "").casefold()
    mapping = {
        "công việc": {"Quan lộc"}, "sự nghiệp": {"Quan lộc"}, "nghề nghiệp": {"Quan lộc"},
        "tiền": {"Tài bạch"}, "tài chính": {"Tài bạch"}, "tài lộc": {"Tài bạch"},
        "hôn nhân": {"Phu thê"}, "tình cảm": {"Phu thê"}, "vợ chồng": {"Phu thê"},
        "con cái": {"Tử tức"}, "sức khỏe": {"Tật ách"}, "bệnh": {"Tật ách"},
        "nhà cửa": {"Điền trạch"}, "bất động sản": {"Điền trạch"},
        "cha mẹ": {"Phụ mẫu"}, "gia đình": {"Phụ mẫu", "Phúc đức"},
        "bạn bè": {"Nô bộc"}, "quan hệ": {"Nô bộc"},
    }
    selected_names: set[str] = set()
    for key, names in mapping.items():
        if key in q:
            selected_names.update(names)
    return {n for n, p in palaces.items() if p.get("cung") in selected_names}


def build_filtered_ai_payload(chart: dict[str, Any], van: dict[str, Any] | None = None, question: str = "") -> dict[str, Any]:
    van = van or {}
    palaces = _palaces(chart)
    layer_positions = _four_layer_positions(van, (van.get("year") or {}).get("nam"))
    seeds = set().union(*layer_positions.values()) if layer_positions else set()
    seeds.update(_domain_seeds(question, palaces))
    try:
        mệnh = next((n for n,p in palaces.items() if p.get("cung") == "Mệnh"), None)
        if mệnh is not None: seeds.add(mệnh)
    except Exception:
        pass
    if not seeds:
        seeds = set(palaces)
    selected, relations = _expand_relations(palaces, seeds)
    selected = {n for n in selected if n in palaces}
    selected_palaces = {str(n): palaces[n] for n in sorted(selected)}

    current = {
        "dai_van": deepcopy(van.get("dai_van", {}).get("dang_xet", {})),
        "luu_nien_dai_van": deepcopy(van.get("luu_nien_dai_van", {})),
        "tieu_van": deepcopy(van.get("tieu_van", {})),
        "luu_nien_nam": deepcopy(van.get("luu_nien_nam", van.get("luu_nien_tieu_van", {}))),
    }
    four = {
        "dai_van": deepcopy(van.get("dai_van_10_nam", {})),
        "luu_nien_dai_van_10_nam": deepcopy(van.get("luu_nien_dai_van_10_nam", [])),
        "tieu_van_10_nam": deepcopy(van.get("tieu_van_10_nam", [])),
        "luu_nien_nam_10_nam": deepcopy(van.get("luu_nien_nam_10_nam", van.get("luu_nien_tieu_van_10_nam", []))),
    }
    return {
        "schema_version": "3.0-ai-payload-filter",
        "question": question,
        "current_year": (van.get("year") or {}).get("nam"),
        "four_han_layers": current,
        "four_han_layers_10_years": four,
        "selected_palaces": selected_palaces,
        "selected_cung_so": sorted(selected),
        "palace_relations": relations,
        "relationship_knowledge": deepcopy(_RELATION_DATA),
        "selection_policy": {
            "always_keep_four_layers": True,
            "always_keep_menh": True,
            "expand": ["tam_hop", "xung_chieu", "nhi_hop", "giap_cung"],
            "keep_all_stars_in_selected_palaces": True,
            "dynamic_van_fields_removed_from_natal_palaces": True,
            "no_astrological_interpretation_performed_by_filter": True,
        },
    }

__all__ = ["build_filtered_ai_payload"]
