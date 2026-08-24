"""Deterministic palace relationship resolver.

All palace-to-palace relationships are derived from the palace Earthly Branch
(dia_chi), never from the visual grid position or from an LLM guess.
"""
from __future__ import annotations

from typing import Any
import re
import unicodedata

BRANCH_ORDER = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
BRANCH_INDEX = {branch: i for i, branch in enumerate(BRANCH_ORDER)}

LUC_HOP_MAP = {
    "Tý": "Sửu", "Sửu": "Tý",
    "Dần": "Hợi", "Hợi": "Dần",
    "Mão": "Tuất", "Tuất": "Mão",
    "Thìn": "Dậu", "Dậu": "Thìn",
    "Tỵ": "Thân", "Thân": "Tỵ",
    "Ngọ": "Mùi", "Mùi": "Ngọ",
}


def normalize_branch(value: Any) -> str | None:
    """Normalize all known engine/gateway Địa Chi representations."""
    if value is None:
        return None
    raw = str(value).strip().casefold()
    direct = {
        "tý": "Tý", "ty": "Tý", "ty1": "Tý",
        "tỵ": "Tỵ", "tị": "Tỵ", "ti": "Tỵ", "ty2": "Tỵ",
        "sửu": "Sửu", "suu": "Sửu",
        "dần": "Dần", "dan": "Dần",
        "mão": "Mão", "mao": "Mão",
        "thìn": "Thìn", "thin": "Thìn",
        "ngọ": "Ngọ", "ngo": "Ngọ",
        "mùi": "Mùi", "mui": "Mùi",
        "thân": "Thân", "than": "Thân",
        "dậu": "Dậu", "dau": "Dậu",
        "tuất": "Tuất", "tuat": "Tuất",
        "hợi": "Hợi", "hoi": "Hợi",
    }
    if raw in direct:
        return direct[raw]
    no_marks = unicodedata.normalize("NFD", raw)
    no_marks = "".join(c for c in no_marks if unicodedata.category(c) != "Mn")
    no_marks = re.sub(r"\d+$", "", no_marks)
    return {
        "ty": "Tý", "suu": "Sửu", "dan": "Dần", "mao": "Mão", "thin": "Thìn",
        "ngo": "Ngọ", "mui": "Mùi", "than": "Thân", "dau": "Dậu", "tuat": "Tuất", "hoi": "Hợi",
    }.get(no_marks)


def _palace_name_by_branch(cungs: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, palace in cungs.items():
        if not isinstance(palace, dict):
            continue
        branch = normalize_branch(palace.get("dia_chi"))
        if branch in BRANCH_INDEX:
            result[branch] = palace.get("cung") or key
    return result


def resolve_palace_relationships(cungs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve Nhị Hợp from the 12 Earthly Branches, not from LLM reasoning."""
    by_branch = _palace_name_by_branch(cungs)
    result: dict[str, dict[str, Any]] = {}
    for key, palace in cungs.items():
        if not isinstance(palace, dict):
            continue
        name = palace.get("cung") or key
        raw_branch = palace.get("dia_chi")
        branch = normalize_branch(raw_branch)
        if branch not in BRANCH_INDEX:
            result[name] = {"nhị_hợp": None, "status": "missing_dia_chi"}
            continue
        partner_branch = LUC_HOP_MAP[branch]
        partner_name = by_branch.get(partner_branch)
        result[name] = {
            "cung": name,
            "dia_chi": raw_branch,
            "dia_chi_chuan": branch,
            "nhị_hợp": {
                "cung": partner_name,
                "dia_chi": partner_branch,
                "method": "Lục Hợp theo Địa Chi",
                "deterministic": True,
                "pair": f"{branch}-{partner_branch}",
            },
            "status": "ok" if partner_name else "missing_partner",
        }
    return result


def attach_palace_relationships(chart: dict[str, Any]) -> dict[str, Any]:
    """Attach deterministic relationship evidence to a chart."""
    if not isinstance(chart, dict):
        raise TypeError("chart phải là dict")
    cungs = chart.get("12_cung", {})
    if not isinstance(cungs, dict):
        return chart
    relationships = resolve_palace_relationships(cungs)
    result = dict(chart)
    result["quan_he_cung"] = relationships
    updated_cungs = {}
    for key, palace in cungs.items():
        if not isinstance(palace, dict):
            updated_cungs[key] = palace
            continue
        name = palace.get("cung") or key
        copy = dict(palace)
        copy["quan_he_cung"] = relationships.get(name, {})
        updated_cungs[key] = copy
    result["12_cung"] = updated_cungs
    return result


__all__ = ["BRANCH_ORDER", "LUC_HOP_MAP", "normalize_branch", "resolve_palace_relationships", "attach_palace_relationships"]
