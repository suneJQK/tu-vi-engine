"""Relationship-aware evaluator for declarative Tử Vi Cách Cục rules."""
from __future__ import annotations

from typing import Any, Iterable

from ..star_registry import has_star as registry_has_star, normalize_star_name, stars_in

BRANCH_LUC_HOP = {
    "Tý": "Sửu", "Sửu": "Tý", "Dần": "Hợi", "Hợi": "Dần",
    "Mão": "Tuất", "Tuất": "Mão", "Thìn": "Dậu", "Dậu": "Thìn",
    "Tỵ": "Thân", "Thân": "Tỵ", "Ngọ": "Mùi", "Mùi": "Ngọ",
}

RELATION_KEYS = ("dong_cung", "tam_phuong_tu_chinh", "tam_hop", "xung_chieu", "nhi_hop", "giap_cung")
TAM_PHUONG_ALIASES = {
    "tam_phuong_tu_chinh_aux", "tam_phuong_tu_chinh_loc", "tam_phuong_sat",
    "tam_phuong_loc", "tam_phuong_ma", "tam_phuong_tuong",
}


def _palaces(chart: dict[str, Any]) -> list[dict[str, Any]]:
    raw = chart.get("12_cung") or chart.get("dia_ban") or {}
    items = list(raw.values()) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
    return [p for p in items if isinstance(p, dict)]


def _normalize_names(names: Iterable[str]) -> set[str]:
    return {normalize_star_name(name) for name in names if str(name).strip()}


def _normalize_palace_name(value: Any) -> str:
    return str(value or "").strip().casefold().split("·", 1)[0].strip()


def _star_records(palace: dict[str, Any]) -> list[dict[str, Any]]:
    return stars_in(palace)


def _star_names(palace: dict[str, Any]) -> set[str]:
    return {normalize_star_name(star.get("ten")) for star in stars_in(palace) if star.get("ten")}


def _star_attribute_matches(star: dict[str, Any], attr: str) -> bool:
    requested = normalize_star_name(attr)
    actual = normalize_star_name(star.get("attribute") or star.get("dac_tinh") or star.get("saoDacTinh"))
    return requested in actual


def _cung_so(palace: dict[str, Any]) -> int | None:
    try:
        value = int(palace.get("cung_so"))
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= 12 else None


def _cung_name(palace: dict[str, Any]) -> str:
    return str(palace.get("cung") or palace.get("cung_ten") or "").strip()


def get_cung_chi(cung: dict[str, Any] | None) -> str:
    if not isinstance(cung, dict):
        return ""
    value = cung.get("dia_chi") or cung.get("chi")
    if value:
        return str(value).strip()
    parts = _cung_name(cung).split()
    return parts[-1] if parts else ""


def _cung_chi(palace: dict[str, Any]) -> str:
    return get_cung_chi(palace)


def get_cung_by_chu(chart: dict[str, Any], name: str) -> dict[str, Any] | None:
    target = _normalize_palace_name(name)
    for palace in _palaces(chart):
        if _normalize_palace_name(_cung_name(palace)) == target or _normalize_palace_name(palace.get("cung_chu")) == target:
            return palace
    return None


def get_cung_by_so(chart: dict[str, Any], cung_so: int) -> dict[str, Any] | None:
    wanted = ((int(cung_so) - 1) % 12) + 1
    return next((p for p in _palaces(chart) if _cung_so(p) == wanted), None)


def get_cung_by_chi(chart: dict[str, Any], chi: str) -> dict[str, Any] | None:
    target = str(chi).strip().casefold()
    return next((p for p in _palaces(chart) if _cung_chi(p).casefold() == target), None)


def _offset_palace(chart: dict[str, Any], target: dict[str, Any], offset: int) -> list[dict[str, Any]]:
    base = _cung_so(target)
    if base is None:
        return []
    wanted = ((base - 1 + offset) % 12) + 1
    return [p for p in _palaces(chart) if _cung_so(p) == wanted]


def related_palaces(chart: dict[str, Any], target: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    dong = [target]
    tam_hop = _offset_palace(chart, target, 4) + _offset_palace(chart, target, 8)
    xung = _offset_palace(chart, target, 6)
    giap = _offset_palace(chart, target, -1) + _offset_palace(chart, target, 1)
    tam_phuong = dong + tam_hop + xung
    partner = BRANCH_LUC_HOP.get(_cung_chi(target))
    luc_hop = []
    if partner:
        found = get_cung_by_chi(chart, partner)
        if found is not None:
            luc_hop = [found]
    return {"dong_cung": dong, "tam_hop": tam_hop, "xung_chieu": xung, "nhi_hop": luc_hop, "giap_cung": giap, "tam_phuong_tu_chinh": tam_phuong}


def get_tam_phuong_tu_chinh(chart: dict[str, Any], cung_so: int) -> list[dict[str, Any]]:
    target = get_cung_by_so(chart, cung_so)
    return related_palaces(chart, target)["tam_phuong_tu_chinh"] if target else []


def get_giap_cung(chart: dict[str, Any], cung_so: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    target = get_cung_by_so(chart, cung_so)
    if target is None:
        return None, None
    rel = related_palaces(chart, target)["giap_cung"]
    return (rel[0] if rel else None, rel[1] if len(rel) > 1 else None)


def get_luc_hop_cung(chart: dict[str, Any], cung_so: int) -> dict[str, Any] | None:
    target = get_cung_by_so(chart, cung_so)
    if target is None:
        return None
    rel = related_palaces(chart, target)["nhi_hop"]
    return rel[0] if rel else None


def has_star(palace: dict[str, Any] | None, star_name: str, star_attr: str | None = None) -> bool:
    if palace is None:
        return False
    return registry_has_star(palace, star_name, star_attr)


def count_stars_in_houses(houses: list[dict[str, Any]], star_names: list[str]) -> int:
    return sum(1 for name in star_names if any(has_star(house, name) for house in houses))


def _scope_star_names(houses: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for house in houses:
        result |= _star_names(house)
    return result


def _scope_matches(scope: list[dict[str, Any]], condition: dict[str, Any]) -> bool:
    stars = _scope_star_names(scope)
    if "stars_all" in condition and not _normalize_names(condition["stars_all"]).issubset(stars): return False
    if "stars_any" in condition and not (_normalize_names(condition["stars_any"]) & stars): return False
    if "stars_none" in condition and (_normalize_names(condition["stars_none"]) & stars): return False
    if "not_both" in condition and _normalize_names(condition["not_both"]).issubset(stars): return False
    if "stars_required" in condition:
        required = _normalize_names(condition["stars_required"])
        if len(required & stars) < int(condition.get("min_count", len(required))): return False
    return True


def match_house_condition(palace: dict[str, Any] | None, condition: dict[str, Any]) -> bool:
    if palace is None: return False
    if "branches_in" in condition and _cung_chi(palace) not in set(condition["branches_in"]): return False
    if "stars_all" in condition and not all(has_star(palace, star) for star in condition["stars_all"]): return False
    if "stars_any" in condition and not any(has_star(palace, star) for star in condition["stars_any"]): return False
    if "stars_none" in condition and any(has_star(palace, star) for star in condition["stars_none"]): return False
    if "not_both" in condition and all(has_star(palace, star) for star in condition["not_both"]): return False
    return True


def _evaluate_tam_phuong_alias(chart: dict[str, Any], target: dict[str, Any], condition: dict[str, Any]) -> bool:
    scope = related_palaces(chart, target)["tam_phuong_tu_chinh"]
    return bool(scope) and _scope_matches(scope, condition)


def evaluate_condition(chart: dict[str, Any], condition: dict[str, Any]) -> bool:
    if not isinstance(condition, dict): return False
    if "any_of" in condition: return any(evaluate_condition(chart, x) for x in condition["any_of"] if isinstance(x, dict))
    if "all_of" in condition:
        branches = [x for x in condition["all_of"] if isinstance(x, dict)]
        return bool(branches) and all(evaluate_condition(chart, x) for x in branches)
    if "cung_menh" in condition:
        nested = {"target": "Mệnh", **condition["cung_menh"]}
        remainder = {k: v for k, v in condition.items() if k != "cung_menh"}
        nested.update(remainder)
        return evaluate_condition(chart, nested)

    target = get_cung_by_chu(chart, str(condition.get("target", "Mệnh")))
    if target is None: return False
    relations = related_palaces(chart, target)
    relation_present = False

    for relation_name in RELATION_KEYS:
        rule = condition.get(relation_name)
        if rule is None: continue
        relation_present = True
        scope = relations[relation_name]
        if not scope: return False
        if rule is True: continue
        if not isinstance(rule, dict) or not _scope_matches(scope, rule): return False

    for alias in TAM_PHUONG_ALIASES:
        if alias in condition:
            relation_present = True
            rule = condition[alias]
            if not isinstance(rule, dict) or not _evaluate_tam_phuong_alias(chart, target, rule): return False

    if "giap_cung_pairs" in condition:
        relation_present = True
        pair_houses = relations["giap_cung"]
        if len(pair_houses) != 2: return False
        matched = False
        for pair in condition["giap_cung_pairs"] if isinstance(condition["giap_cung_pairs"], list) else []:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2: continue
            first, second = pair
            if (has_star(pair_houses[0], first) and has_star(pair_houses[1], second)) or (has_star(pair_houses[0], second) and has_star(pair_houses[1], first)):
                matched = True
                break
        if not matched: return False

    for key, house_name in (("cung_quan", "Quan Lộc"), ("cung_tai", "Tài Bạch"), ("cung_dien", "Điền Trạch")):
        if key in condition:
            relation_present = True
            if not match_house_condition(get_cung_by_chu(chart, house_name), condition[key]): return False

    for key, chi in (("cung_ty", "Tỵ"), ("cung_dau", "Dậu")):
        if key in condition:
            relation_present = True
            if not match_house_condition(get_cung_by_chi(chart, chi), condition[key]): return False

    if "luc_hop" in condition:
        relation_present = True
        partner = relations["nhi_hop"]
        if not partner or not match_house_condition(partner[0], condition["luc_hop"]): return False

    target_filters = {key: condition[key] for key in ("branches_in", "stars_all", "stars_any", "stars_none", "not_both") if key in condition}
    if target_filters and not match_house_condition(target, target_filters): return False

    if "stem_contains" in condition:
        relation_present = True
        can_nam = str((chart.get("thien_ban") or {}).get("can_nam") or "")
        if str(condition["stem_contains"]) not in can_nam: return False

    return relation_present or bool(target_filters)


__all__ = ["get_cung_chi", "get_cung_by_chu", "get_cung_by_so", "get_cung_by_chi", "related_palaces", "get_tam_phuong_tu_chinh", "get_giap_cung", "get_luc_hop_cung", "has_star", "count_stars_in_houses", "evaluate_condition"]
