"""Compatibility wrapper: authoritative 10-year Dai Van / Tieu Van / Luu Nien Nam layers."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from .van_calculator_legacy import *  # noqa: F401,F403
from . import van_calculator_legacy as _legacy

BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
CAN_NAMES = {1: "Giáp", 2: "Ất", 3: "Bính", 4: "Đinh", 5: "Mậu", 6: "Kỷ", 7: "Canh", 8: "Tân", 9: "Nhâm", 10: "Quý"}
BRANCH_NAMES = {index + 1: branch for index, branch in enumerate(BRANCHES)}


def _normalize_branch(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().casefold()
    direct = {
        "tý": "Tý", "ty": "Tý", "ty1": "Tý",
        "tỵ": "Tỵ", "ty2": "Tỵ", "tị": "Tỵ", "ti": "Tỵ",
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
    normalized = unicodedata.normalize("NFD", raw)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"\d+$", "", normalized)
    fallback = {
        "ty": "Tý", "suu": "Sửu", "dan": "Dần", "mao": "Mão", "thin": "Thìn",
        "ti": "Tỵ", "ty2": "Tỵ", "ngo": "Ngọ", "mui": "Mùi", "than": "Thân",
        "dau": "Dậu", "tuat": "Tuất", "hoi": "Hợi",
    }
    return fallback.get(normalized)


def _palace_by_number(chart: dict[str, Any], palace_number: Any) -> dict[str, Any] | None:
    try:
        number = int(palace_number)
    except (TypeError, ValueError):
        return None
    for palace in (chart.get("12_cung") or {}).values():
        if isinstance(palace, dict) and int(palace.get("cung_so", 0) or 0) == number:
            return palace
    return None


def _palace_by_branch(chart: dict[str, Any], branch: Any) -> dict[str, Any] | None:
    target = _normalize_branch(branch)
    if target is None:
        return None
    for palace in (chart.get("12_cung") or {}).values():
        if not isinstance(palace, dict):
            continue
        palace_branch = _normalize_branch(palace.get("dia_chi"))
        if palace_branch == target:
            return palace
    return None


def _direction_from_dv(van: dict[str, Any]) -> int:
    return 1 if ((van.get("dai_van") or {}).get("huong") or "thuận") == "thuận" else -1


def _authoritative_luu_nien_dai_van_cung(cung_dai_van: int, year_index: int, direction: int) -> int:
    """0=Đại vận; 1=Xung chiếu; từ năm 3 dịch ngược chiều vòng vận."""
    if year_index == 0:
        return _legacy.check(cung_dai_van)
    if year_index == 1:
        return _legacy.check(cung_dai_van + 6)
    movement = -direction
    return _legacy.check(cung_dai_van + 6 + (year_index - 1) * movement)


def _build_luu_nien_dai_van_10_nam(chart: dict[str, Any], van: dict[str, Any]) -> list[dict[str, Any]]:
    dv = (van.get("dai_van") or {}).get("dang_xet") or {}
    if not dv:
        return []
    start_age = int(dv["tuoi_bat_dau"])
    start_year = int(chart.get("input", {}).get("nam")) + start_age - 1
    direction = _direction_from_dv(van)
    rows: list[dict[str, Any]] = []
    for idx in range(10):
        age = start_age + idx
        target_year = start_year + idx
        cung_so = _authoritative_luu_nien_dai_van_cung(int(dv["cung_so"]), idx, direction)
        palace = _palace_by_number(chart, cung_so)
        rows.append({
            "nam": target_year,
            "tuoi": age,
            "nam_thu": idx + 1,
            "cung_so": cung_so,
            "cung": palace.get("cung") if palace else None,
            "dia_chi": palace.get("dia_chi") if palace else None,
            "can_chi": palace.get("can_chi") if palace else None,
            "la_nam_dang_xem": target_year == (van.get("year") or {}).get("nam"),
            "cach_tinh": (
                "Năm 1 = cung Đại vận; Năm 2 = cung xung chiếu; "
                "Năm 3 = xung chiếu ±1 theo chiều đối ứng; từ năm 4 tiếp tục cùng chiều."
            ),
        })
    return rows


def _build_tieu_van_10_nam(chart: dict[str, Any], van: dict[str, Any]) -> list[dict[str, Any]]:
    dv = (van.get("dai_van") or {}).get("dang_xet") or {}
    birth_branch = _legacy._birth_year_branch(chart)
    if not dv or birth_branch is None:
        return []
    start_age = int(dv["tuoi_bat_dau"])
    start_year = int(chart.get("input", {}).get("nam")) + start_age - 1
    gender = str(chart.get("input", {}).get("gioi_tinh", "Nam"))
    rows: list[dict[str, Any]] = []
    for idx in range(10):
        age = start_age + idx
        target_year = start_year + idx
        _can, target_branch = _legacy.can_chi_year(target_year)
        mapping = _legacy._tieu_van_source_mapping(birth_branch, target_branch, gender)
        cung_so = mapping.get("cung_so")
        palace = _palace_by_branch(chart, mapping.get("cung_dia_chi"))
        if palace is None:
            palace = _palace_by_number(chart, cung_so)
        rows.append({
            "nam": target_year,
            "tuoi": age,
            "nam_thu": idx + 1,
            "chi_nam": target_branch,
            "chi_ten": _legacy.chi_name(target_branch),
            "cung_so": palace.get("cung_so") if palace else cung_so,
            "cung": palace.get("cung") if palace else None,
            "dia_chi": palace.get("dia_chi") if palace else None,
            "can_chi": palace.get("can_chi") if palace else None,
            "cung_khoi": mapping.get("cung_khoi"),
            "huong": mapping.get("huong"),
            "la_nam_dang_xem": target_year == (van.get("year") or {}).get("nam"),
            "cach_tinh": "Cung khởi làm mốc Tý, dịch theo Chi năm xem theo quy tắc Tiểu vận của engine.",
        })
    return rows


def _build_luu_nien_nam_10_nam(chart: dict[str, Any], van: dict[str, Any]) -> list[dict[str, Any]]:
    """Lưu niên năm: từng năm lấy Chi của chính năm đó -> cung có cùng Địa Chi trên lá số."""
    dv = (van.get("dai_van") or {}).get("dang_xet") or {}
    current_year = (van.get("year") or {}).get("nam")
    if not dv or current_year is None:
        return []

    start_age = int(dv["tuoi_bat_dau"])
    start_year = int(chart.get("input", {}).get("nam")) + start_age - 1
    rows: list[dict[str, Any]] = []
    for idx in range(10):
        age = start_age + idx
        target_year = start_year + idx
        can_no, target_branch = _legacy.can_chi_year(target_year)
        target_branch_name = _normalize_branch(target_branch) or str(target_branch)
        palace = _palace_by_branch(chart, target_branch_name)
        chi_number = None
        if target_branch_name in BRANCHES:
            chi_number = BRANCHES.index(target_branch_name) + 1
        rows.append({
            "nam": target_year,
            "tuoi": age,
            "nam_thu": idx + 1,
            "can": can_no,
            "chi": chi_number,
            "can_ten": CAN_NAMES.get(int(can_no)) if can_no is not None else None,
            "chi_ten": target_branch_name,
            "cung_so": palace.get("cung_so") if palace else None,
            "cung": palace.get("cung") if palace else None,
            "dia_chi": palace.get("dia_chi") if palace else None,
            "can_chi": palace.get("can_chi") if palace else None,
            "la_nam_dang_xem": target_year == current_year,
            "cach_tinh": "Lưu niên năm = lấy Chi của chính năm xem và đặt vào cung có cùng Địa Chi trên lá số.",
            "source_of_truth": "can_chi_year + cung Địa Chi thực tế của lá số",
        })
    return rows


def calculate_van_layers(
    chart: dict[str, Any],
    *,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    hour: int | None = None,
    time_zone: float | None = None,
) -> dict[str, Any]:
    van = _legacy.calculate_van_layers(
        chart, year=year, month=month, day=day, hour=hour, time_zone=time_zone
    )

    direction = _direction_from_dv(van)
    dv10 = _build_luu_nien_dai_van_10_nam(chart, van)
    tv10 = _build_tieu_van_10_nam(chart, van)
    ln10 = _build_luu_nien_nam_10_nam(chart, van)

    van["luu_nien_dai_van_10_nam"] = dv10
    van["tieu_van_10_nam"] = tv10
    van["luu_nien_nam_10_nam"] = ln10
    van["luu_nien_tieu_van_10_nam"] = ln10
    van["van_10_nam"] = {
        "dai_van_cung_so": (van.get("dai_van") or {}).get("dang_xet", {}).get("cung_so"),
        "dai_van_tuoi_bat_dau": (van.get("dai_van") or {}).get("dang_xet", {}).get("tuoi_bat_dau"),
        "dai_van_tuoi_ket_thuc": (van.get("dai_van") or {}).get("dang_xet", {}).get("tuoi_ket_thuc"),
        "huong_vong_van": "thuận" if direction == 1 else "nghịch",
        "luu_nien_dai_van": dv10,
        "tieu_van": tv10,
        "luu_nien_nam": ln10,
        "source_of_truth": "tuvi_engine.van_calculator authoritative 4-layer 10-year context",
    }

    current_year = (van.get("year") or {}).get("nam")
    current_dv = next((r for r in dv10 if r["nam"] == current_year), None)
    current_tv = next((r for r in tv10 if r["nam"] == current_year), None)
    current_ln = next((r for r in ln10 if r["nam"] == current_year), None)
    if current_dv:
        van.setdefault("luu_nien", {})["cung_luu_nien_trong_dai_van_authoritative"] = current_dv["cung_so"]
        van.setdefault("luu_nien", {})["luu_nien_dai_van_10_nam"] = dv10
    if current_tv:
        van.setdefault("tieu_van", {})["cung_so_authoritative"] = current_tv["cung_so"]
        van.setdefault("tieu_van", {})["tieu_van_10_nam"] = tv10
    if current_ln:
        van["luu_nien_nam"] = current_ln
        van["luu_nien_tieu_van"] = current_ln

    van["rules_audit"] = {
        **(van.get("rules_audit") or {}),
        "four_han_layers": {
            "dai_van": "Đại vận thực tế của chính lá số, một khoảng 10 năm.",
            "luu_nien_dai_van": "Năm 1 = Đại vận; năm 2 = xung chiếu; năm 3 dịch 1 cung theo chiều đối ứng; năm 4-10 tiếp tục theo quy tắc đã chốt.",
            "tieu_van": "Tính độc lập từng năm theo hệ Tiểu vận của engine.",
            "luu_nien_nam": "Lấy Chi của chính năm xem và tra cung có cùng Địa Chi trên lá số; độc lập với Tiểu vận và Lưu niên Đại vận.",
        },
    }
    return van
