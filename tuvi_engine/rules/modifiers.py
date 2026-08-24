"""Post-match modifiers such as Lộc Phùng Xung Phá."""
from __future__ import annotations

from typing import Any

from ..data_loader import load_json
from .evaluator import _scope_star_names, has_star, related_palaces


def _palaces(chart: dict[str, Any]) -> list[dict[str, Any]]:
    raw = chart.get("12_cung") or chart.get("dia_ban") or {}
    return list(raw.values()) if isinstance(raw, dict) else list(raw) if isinstance(raw, list) else []


def _label(palace: dict[str, Any]) -> dict[str, Any]:
    return {
        "cung_so": palace.get("cung_so"),
        "cung": palace.get("cung") or palace.get("cung_ten"),
        "dia_chi": palace.get("dia_chi") or palace.get("chi"),
    }


def detect_cach_cuc_modifiers(chart: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = load_json("data/cach_cuc_modifiers.json")
    modifiers = catalog.get("modifiers", {}) if isinstance(catalog, dict) else {}
    loc_rule = modifiers.get("loc_phung_xung_pha")
    if not isinstance(loc_rule, dict):
        return []

    target_stars = [str(x) for x in loc_rule.get("target_stars", [])]
    breaking = loc_rule.get("breaking_factors", {})
    results: list[dict[str, Any]] = []

    for palace in _palaces(chart):
        locs = [star for star in target_stars if has_star(palace, star)]
        if not locs:
            continue
        relations = related_palaces(chart, palace)
        evidence: list[dict[str, Any]] = []
        for relation_name, factors in breaking.items():
            scope = relations.get(relation_name, [])
            matched_factors: list[dict[str, Any]] = []
            for factor in factors if isinstance(factors, list) else []:
                for related in scope:
                    if has_star(related, factor):
                        matched_factors.append({
                            "star": factor,
                            "relation": relation_name,
                            "palace": _label(related),
                        })
            if matched_factors:
                evidence.extend(matched_factors)

        if evidence:
            results.append({
                "id": "loc_phung_xung_pha",
                "name": loc_rule.get("name", "Lộc Phùng Xung Phá"),
                "effect": loc_rule.get("effect", "DEGRADE"),
                "loc_palace": _label(palace),
                "loc_stars": locs,
                "breaking_evidence": evidence,
                "interpretation": loc_rule.get("interpretation", ""),
                "ai_instruction": loc_rule.get("ai_instruction", ""),
            })

    return results


__all__ = ["detect_cach_cuc_modifiers"]
