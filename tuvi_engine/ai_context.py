"""Build deterministic AI context and route it through the payload filter."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .ai_payload_filter import build_filtered_ai_payload
from .data_loader import load_cach_cuc, load_json
from .van_contract import canonicalize_van_layers, validate_van_layer_contract

_RELATION_DATA = load_json("data/relationships_ai.json")


def load_relationship_knowledge() -> dict[str, Any]:
    return deepcopy(_RELATION_DATA)


def _index_cach_cuc(items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(item["id"]): item for item in items if isinstance(item, dict) and item.get("id") is not None}


def _normalize_matched_cach_cuc(chart: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = _index_cach_cuc(catalog)
    analysis = chart.get("cach_cuc_analysis") if isinstance(chart.get("cach_cuc_analysis"), dict) else {}
    matched = analysis.get("matched") if isinstance(analysis.get("matched"), list) else chart.get("cach_cuc", [])
    result: list[dict[str, Any]] = []
    if not isinstance(matched, list):
        return result
    for item in matched:
        if isinstance(item, int) and item in index:
            result.append(deepcopy(index[item]))
        elif isinstance(item, dict):
            item_id = item.get("id")
            try:
                item_id_int = int(item_id) if item_id is not None else None
            except (TypeError, ValueError):
                item_id_int = None
            if item_id_int is not None and item_id_int in index:
                base = deepcopy(index[item_id_int])
                base.update(deepcopy(item))
                result.append(base)
            else:
                result.append(deepcopy(item))
    return result


def _question_scope(question: str) -> dict[str, Any]:
    q = (question or "").strip().casefold()
    if any(x in q for x in ("lưu niên đại vận", "lưu đại hạn", "lưu đại vận")):
        return {"id": "luu_nien_dai_van", "focus": "luu_nien_dai_van", "weights": {"dai_van": 0.25, "luu_nien_dai_van": 0.50, "tieu_van": 0.10, "luu_nien_nam": 0.15}}
    if any(x in q for x in ("tiểu hạn", "tiểu vận")):
        return {"id": "tieu_van", "focus": "tieu_van", "weights": {"dai_van": 0.20, "luu_nien_dai_van": 0.20, "tieu_van": 0.40, "luu_nien_nam": 0.20}}
    if any(x in q for x in ("lưu niên năm", "lưu thái tuế", "thái tuế")):
        return {"id": "luu_nien_nam", "focus": "luu_nien_nam", "weights": {"dai_van": 0.20, "luu_nien_dai_van": 0.15, "tieu_van": 0.20, "luu_nien_nam": 0.45}}
    if any(x in q for x in ("đại vận", "đại hạn", "10 năm", "mười năm")):
        return {"id": "dai_van", "focus": "dai_van", "weights": {"dai_van": 0.80, "relations_and_stars": 0.20}}
    return {"id": "tong_hop_nam", "focus": "tong_hop_nam", "weights": {"dai_van": 0.55, "luu_nien_dai_van": 0.18, "tieu_van": 0.15, "luu_nien_nam": 0.12}}


def build_ai_context(
    chart: dict[str, Any],
    *,
    van: dict[str, Any] | None = None,
    question: str = "",
) -> dict[str, Any]:
    """Build the model-facing context from the deterministic filter.

    Dynamic vận is normalized at this boundary so downstream AI code sees one
    canonical four-layer structure even while legacy aliases remain available
    inside the calculator for backward compatibility.
    """
    if not isinstance(chart, dict):
        raise TypeError("chart phải là dict")

    cach_cuc_catalog = load_cach_cuc()
    van_contract_errors = validate_van_layer_contract(van) if van is not None else []
    canonical_van = canonicalize_van_layers(van) if van is not None else {}
    filtered = build_filtered_ai_payload(chart, van or {}, question)
    scope = _question_scope(question)
    matched_cach_cuc = _normalize_matched_cach_cuc(chart, cach_cuc_catalog)
    modifiers = deepcopy(chart.get("cach_cuc_modifiers", [])) if isinstance(chart.get("cach_cuc_modifiers", []), list) else []
    context: dict[str, Any] = {
        "schema_version": "3.5-ai-context-canonical-four-van-layers",
        "input": deepcopy(chart.get("input", {})),
        "confirmed_cach_cuc": {
            "count": len(matched_cach_cuc),
            "items": matched_cach_cuc,
            "source": "tuvi_engine.rules.cach_cuc.detect_cach_cuc",
            "authoritative": True,
            "allow_ai_invented_names": False,
        },
        "cach_cuc_modifiers": {
            "count": len(modifiers),
            "items": modifiers,
            "source": "tuvi_engine.rules.modifiers.detect_cach_cuc_modifiers",
            "authoritative": True,
            "display_with_cach_cuc": True,
            "allow_ai_invented_names": False,
        },
        "thien_ban": deepcopy(chart.get("thien_ban", {})),
        "palaces": deepcopy(filtered.get("selected_palaces", {})),
        "ai_payload": filtered,
        "relationship_knowledge": load_relationship_knowledge(),
        "matched_cach_cuc": matched_cach_cuc,
        "question_scope": scope,
        "reasoning_contract": {
            "ai_payload_source_of_truth": "ai_payload",
            "use_only_provided_relations": True,
            "use_only_matched_cach_cuc": True,
            "use_only_confirmed_cach_cuc": True,
            "confirmed_cach_cuc_source_of_truth": "confirmed_cach_cuc",
            "cach_cuc_count_source_of_truth": "confirmed_cach_cuc.count",
            "cach_cuc_name_must_match_engine": True,
            "never_invent_cach_cuc_names": True,
            "never_upgrade_star_pattern_to_cach_cuc": True,
            "allow_only_engine_confirmed_cach_cuc": True,
            "modifiers_are_engine_confirmed_data": True,
            "display_modifiers_as_cach_cuc_items_without_good_bad_label": True,
            "do_not_claim_zero_cach_cuc_when_confirmed_cach_cuc_count_positive": True,
            "do_not_invent_missing_stars_or_relations": True,
            "separate_facts_from_interpretation": True,
            "dynamic_van_source_of_truth": "van_han.canonical_layers",
            "never_read_static_tieu_van_from_palaces": True,
            "four_han_layers_required_for_van_questions": True,
            "four_han_layers": ["dai_van", "luu_nien_dai_van", "tieu_van", "luu_nien_nam"],
            "tam_hop_must_include_all_three_palaces": True,
            "name_each_influential_star_and_event": True,
            "filter_never_interprets": True,
            "scope_driven_weighting": True,
            "weights": scope["weights"],
            "van_contract_errors": van_contract_errors,
            "deprecate_luu_nien_tieu_van_alias": True,
            "convergence_rule": {
                "two_layers": "tang_do_tin_cay",
                "three_layers": "su_kien_manh",
                "four_layers_plus_root_transit_star_repetition": "su_kien_trong_diem",
                "not_additive_probability": True,
            },
        },
    }
    if van is not None:
        context["van_han"] = canonical_van
    return context


__all__ = ["build_ai_context", "load_relationship_knowledge"]
