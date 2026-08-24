"""Detect Cách Cục with explicit palace-relationship evidence."""
from __future__ import annotations

from typing import Any

from tuvi_engine.data_loader import load_cach_cuc

from .evaluator import (
    _normalize_names,
    _normalize_palace_name,
    _scope_star_names,
    evaluate_condition,
    get_cung_by_chu,
    related_palaces,
)


def _palace_label(palace: dict[str, Any]) -> dict[str, Any]:
    return {
        "cung_so": palace.get("cung_so"),
        "cung": palace.get("cung") or palace.get("cung_ten"),
        "dia_chi": palace.get("dia_chi") or palace.get("chi"),
    }


def _evidence_for_relation(
    chart: dict[str, Any],
    target: dict[str, Any],
    relation_name: str,
    rule: dict[str, Any],
) -> dict[str, Any]:
    relationships = related_palaces(chart, target)
    palaces = relationships.get(relation_name, [])
    required = _normalize_names(rule.get("stars_required", rule.get("stars_all", [])))

    evidence: dict[str, Any] = {
        "relation": relation_name,
        "required_stars": sorted(required),
        "min_count": rule.get("min_count", len(required)),
        "palaces": [],
    }

    for palace in palaces:
        found_names = _scope_star_names([palace])
        matched = sorted(required & found_names)
        evidence["palaces"].append({
            **_palace_label(palace),
            "matched_stars": matched,
        })

    evidence["matched_count"] = len(required & _scope_star_names(palaces))
    return evidence


def _evidence_for_condition(chart: dict[str, Any], condition: dict[str, Any]) -> dict[str, Any]:
    target_name = str(condition.get("target", "Mệnh"))
    target = get_cung_by_chu(chart, target_name)
    if target is None:
        return {"target": target_name, "matched": False}

    evidence: dict[str, Any] = {
        "target": target_name,
        "target_palace": _palace_label(target),
        "relations": [],
    }

    for relation_name in ("dong_cung", "tam_phuong_tu_chinh", "tam_hop", "xung_chieu", "nhi_hop", "giap_cung"):
        rule = condition.get(relation_name)
        if isinstance(rule, dict):
            evidence["relations"].append(_evidence_for_relation(chart, target, relation_name, rule))

    # Aliases from the TuViMCP rule vocabulary all map to Tam Phương Tứ Chính.
    for alias in ("tam_phuong_tu_chinh_aux", "tam_phuong_tu_chinh_loc", "tam_phuong_sat", "tam_phuong_loc", "tam_phuong_ma", "tam_phuong_tuong"):
        rule = condition.get(alias)
        if isinstance(rule, dict):
            evidence["relations"].append(_evidence_for_relation(chart, target, "tam_phuong_tu_chinh", rule) | {"alias": alias})

    if "giap_cung_pairs" in condition:
        relationships = related_palaces(chart, target)
        pair_houses = relationships["giap_cung"]
        pairs = condition.get("giap_cung_pairs")
        pair_evidence = [_palace_label(palace) for palace in pair_houses]
        evidence["giap_cung_pairs"] = {
            "required_pairs": pairs,
            "palaces": pair_evidence,
        }

    for key, house_name in (("cung_quan", "Quan Lộc"), ("cung_tai", "Tài Bạch"), ("cung_dien", "Điền Trạch")):
        if key in condition:
            palace = get_cung_by_chu(chart, house_name)
            evidence[key] = {
                "palace": _palace_label(palace) if palace else None,
                "condition": condition[key],
            }

    for key, chi in (("cung_ty", "Tỵ"), ("cung_dau", "Dậu")):
        if key in condition:
            evidence[key] = {"chi": chi, "condition": condition[key]}

    if "luc_hop" in condition:
        evidence["luc_hop"] = {"condition": condition["luc_hop"]}

    return evidence


def _matched_branches(chart: dict[str, Any], conditions: dict[str, Any]) -> list[dict[str, Any]]:
    branches = conditions.get("any_of") if isinstance(conditions.get("any_of"), list) else [conditions]
    result = []
    for index, branch in enumerate(branches):
        if not isinstance(branch, dict):
            continue
        if evaluate_condition(chart, branch):
            result.append({
                "branch_index": index,
                "condition": branch,
                "evidence": _evidence_for_condition(chart, branch),
            })
    return result


def detect_cach_cuc(chart: dict[str, Any]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for rule in load_cach_cuc():
        conditions = rule.get("conditions")
        if not isinstance(conditions, dict):
            continue
        branches = _matched_branches(chart, conditions)
        if not branches:
            continue
        matches.append({
            "id": rule.get("id"),
            "name": rule.get("name"),
            "category": rule.get("category"),
            "description": rule.get("description", ""),
            "reason": rule.get("reason", ""),
            "conditions": conditions,
            "matched_branches": branches,
            "interpretation": {
                "co_ca": rule.get("co_ca", ""),
                "binh_chu": rule.get("binh_chu", ""),
                "uu_khuyet_diem": rule.get("uu_khuyet_diem", ""),
            },
        })
    return matches


__all__ = ["detect_cach_cuc"]
