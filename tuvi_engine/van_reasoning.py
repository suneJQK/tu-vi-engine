"""Structured reasoning layer for Tử Vi vận hạn."""
from __future__ import annotations

from typing import Any
import re
import unicodedata

BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
TAM_PHUONG_GROUPS = (
    frozenset(("Thân", "Tý", "Thìn")),
    frozenset(("Dần", "Ngọ", "Tuất")),
    frozenset(("Tỵ", "Dậu", "Sửu")),
    frozenset(("Hợi", "Mão", "Mùi")),
)
NHI_HOP = {
    frozenset(("Tý", "Sửu")),
    frozenset(("Hợi", "Dần")),
    frozenset(("Tuất", "Mão")),
    frozenset(("Thìn", "Dậu")),
    frozenset(("Tỵ", "Thân")),
    frozenset(("Ngọ", "Mùi")),
}
LAYER_WEIGHTS = {
    "nguyen_cuc": 100,
    "dai_van": 80,
    "luu_dai_van": 75,
    "luu_nien": 70,
    "tieu_van": 60,
    "luu_nguyet": 45,
    "luu_nhat": 30,
    "luu_thoi": 20,
}


def _branch_name(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().casefold()
    direct = {
        "tý": "Tý", "tỵ": "Tỵ", "sửu": "Sửu", "dần": "Dần", "mão": "Mão",
        "thìn": "Thìn", "ngọ": "Ngọ", "mùi": "Mùi", "thân": "Thân",
        "dậu": "Dậu", "tuất": "Tuất", "hợi": "Hợi",
        "ty1": "Tý", "ty2": "Tỵ", "suu": "Sửu", "dan": "Dần", "mao": "Mão",
        "thin": "Thìn", "ngo": "Ngọ", "mui": "Mùi", "than": "Thân", "dau": "Dậu",
        "tuat": "Tuất", "hoi": "Hợi",
    }
    if raw in direct:
        return direct[raw]
    no_marks = unicodedata.normalize("NFD", raw)
    no_marks = "".join(c for c in no_marks if unicodedata.category(c) != "Mn")
    no_marks = re.sub(r"\d+$", "", no_marks)
    fallback = {
        "ty": "Tý", "suu": "Sửu", "dan": "Dần", "mao": "Mão", "thin": "Thìn",
        "ngo": "Ngọ", "mui": "Mùi", "than": "Thân", "dau": "Dậu", "tuat": "Tuất", "hoi": "Hợi",
    }
    return fallback.get(no_marks)


def _branch_index(value: Any) -> int | None:
    name = _branch_name(value)
    return BRANCHES.index(name) if name in BRANCHES else None


def _palace_map(chart: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for palace in (chart.get("12_cung") or {}).values():
        if isinstance(palace, dict) and isinstance(palace.get("cung_so"), int):
            out[palace["cung_so"]] = palace
    return out


def _palace_by_number(chart: dict[str, Any], number: Any) -> dict[str, Any] | None:
    try:
        return _palace_map(chart).get(int(number))
    except (TypeError, ValueError):
        return None


def _stars(palace: dict[str, Any] | None) -> list[str]:
    if not palace:
        return []
    return [str(s["ten"]) for s in (palace.get("sao") or []) if isinstance(s, dict) and s.get("ten")]


def _relation(a: Any, b: Any) -> str:
    a_name = _branch_name(a)
    b_name = _branch_name(b)
    if not a_name or not b_name:
        return "khac"
    if a_name == b_name:
        return "dong_cung"
    if any(a_name in group and b_name in group for group in TAM_PHUONG_GROUPS):
        return "tam_hop"
    ia = _branch_index(a_name)
    ib = _branch_index(b_name)
    if ia is not None and ib is not None and (ib - ia) % 12 == 6:
        return "xung_chieu"
    if frozenset((a_name, b_name)) in NHI_HOP:
        return "nhi_hop"
    return "khac"


def _relation_between_palaces(base: dict[str, Any], other: dict[str, Any]) -> str:
    base_no = base.get("cung_so")
    other_no = other.get("cung_so")
    if base_no == other_no:
        return "dong_cung"
    if isinstance(base_no, int) and isinstance(other_no, int):
        diff = (other_no - base_no) % 12
        if diff in (1, 11):
            return "giap_cung"
    return _relation(base.get("dia_chi"), other.get("dia_chi"))


def _interactions(chart: dict[str, Any], target: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for palace in (chart.get("12_cung") or {}).values():
        if not isinstance(palace, dict) or palace.get("cung_so") == target.get("cung_so"):
            continue
        rel = _relation_between_palaces(target, palace)
        if rel in {"tam_hop", "xung_chieu", "nhi_hop", "giap_cung"}:
            result.append({
                "quan_he": rel,
                "cung_so": palace.get("cung_so"),
                "cung": palace.get("cung"),
                "dia_chi": palace.get("dia_chi"),
                "dia_chi_chuan": _branch_name(palace.get("dia_chi")),
                "can_chi": palace.get("can_chi"),
                "stars": _stars(palace),
            })
    order = {"tam_hop": 0, "xung_chieu": 1, "nhi_hop": 2, "giap_cung": 3}
    result.sort(key=lambda x: (order.get(x["quan_he"], 99), int(x.get("cung_so") or 0)))
    return result


def _activated_refs(chart: dict[str, Any], van: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    sources = (
        ("dai_van", (van.get("dai_van") or {}).get("dang_xet")),
        ("luu_dai_van", van.get("luu_dai_van")),
        ("luu_nien", van.get("luu_nien") or van.get("year")),
        ("tieu_van", van.get("tieu_van")),
        ("luu_nguyet", van.get("luu_nguyet")),
        ("luu_nhat", van.get("luu_nhat")),
        ("luu_thoi", van.get("luu_thoi")),
    )
    for layer, data in sources:
        if not isinstance(data, dict):
            continue
        palace = _palace_by_number(chart, data.get("cung_so"))
        if palace:
            refs.append({"layer": layer, "source": data, "palace": palace})
    return refs


def _tieu_van_tam_phuong_tu_chinh(chart: dict[str, Any], van: dict[str, Any]) -> dict[str, Any]:
    tieu = van.get("tieu_van") or {}
    target = _palace_by_number(chart, tieu.get("cung_so"))
    if not target:
        return {"cung_tieu_van": None, "tam_phuong": [], "xung_chieu": None, "nhi_hop": None, "giap_cung": []}
    tam_phuong = []
    xung = None
    nhi = None
    giap = []
    for palace in (chart.get("12_cung") or {}).values():
        if not isinstance(palace, dict) or palace.get("cung_so") == target.get("cung_so"):
            continue
        rel = _relation_between_palaces(target, palace)
        item = {
            "cung_so": palace.get("cung_so"),
            "cung": palace.get("cung"),
            "dia_chi": palace.get("dia_chi"),
            "dia_chi_chuan": _branch_name(palace.get("dia_chi")),
            "can_chi": palace.get("can_chi"),
            "stars": _stars(palace),
        }
        if rel == "tam_hop": tam_phuong.append(item)
        elif rel == "xung_chieu": xung = item
        elif rel == "nhi_hop": nhi = item
        elif rel == "giap_cung": giap.append(item)
    tam_phuong.sort(key=lambda x: int(x.get("cung_so") or 0))
    giap.sort(key=lambda x: int(x.get("cung_so") or 0))
    return {
        "cung_tieu_van": {
            "cung_so": target.get("cung_so"),
            "cung": target.get("cung"),
            "dia_chi": target.get("dia_chi"),
            "dia_chi_chuan": _branch_name(target.get("dia_chi")),
            "can_chi": target.get("can_chi"),
            "stars": _stars(target),
        },
        "tam_phuong": tam_phuong,
        "xung_chieu": xung,
        "nhi_hop": nhi,
        "giap_cung": giap,
        "rule": {
            "tam_phuong": ["Thân-Tý-Thìn", "Dần-Ngọ-Tuất", "Tỵ-Dậu-Sửu", "Hợi-Mão-Mùi"],
            "xung_chieu": "cung_so đối diện, cách 6",
            "giap_cung": "cung_so +1 và -1 theo vòng 12 cung",
            "nhi_hop": ["Tý-Sửu", "Hợi-Dần", "Tuất-Mão", "Thìn-Dậu", "Tỵ-Thân", "Ngọ-Mùi"],
        },
        "anti_confusion": "Xác định quan hệ theo vị trí/Địa Chi thực tế trước, sau đó mới gắn tên cung chức năng.",
    }


def build_reasoning_context(chart: dict[str, Any], van: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    for ref in _activated_refs(chart, van):
        p = ref["palace"]
        layer = ref["layer"]
        evidence.append({
            "layer": layer,
            "priority": LAYER_WEIGHTS.get(layer, 0),
            "cung_so": p.get("cung_so"),
            "cung": p.get("cung"),
            "dia_chi": p.get("dia_chi"),
            "dia_chi_chuan": _branch_name(p.get("dia_chi")),
            "chinh_tinh": [s.get("ten") for s in p.get("chinh_tinh", []) if isinstance(s, dict)],
            "phu_tinh": [s.get("ten") for s in p.get("phu_tinh", []) if isinstance(s, dict)],
            "stars": _stars(p),
            "tuan_triet": {"tuan": bool(p.get("tuan")), "triet": bool(p.get("triet"))},
            "interactions": _interactions(chart, p),
        })
    evidence.sort(key=lambda x: -x["priority"])
    return {
        "engine": "van_reasoning_v3",
        "workflow": [
            "Xác định tầng vận và cung thực tế trước khi gắn tên cung chức năng.",
            "Tam phương theo 4 tổ hợp: Thân-Tý-Thìn; Dần-Ngọ-Tuất; Tỵ-Dậu-Sửu; Hợi-Mão-Mùi.",
            "Xung chiếu là cung đối diện, cung_so cách 6.",
            "Giáp cung là cung trước và sau, cung_so +1 và -1 theo vòng 12 cung.",
            "Nhị hợp là Tý-Sửu; Hợi-Dần; Tuất-Mão; Thìn-Dậu; Tỵ-Thân; Ngọ-Mùi.",
            "Chồng các tầng: Nguyên cục -> Đại vận -> Lưu Đại vận -> Lưu niên -> Tiểu vận -> Lưu nguyệt -> Lưu nhật -> Lưu thời.",
        ],
        "active_layers": evidence,
        "tieu_van_tam_phuong_tu_chinh": _tieu_van_tam_phuong_tu_chinh(chart, van),
        "principles": {
            "dai_van": "lớp nền dài hạn",
            "luu_dai_van": "lớp chuyển động trong Đại vận",
            "luu_nien": "kích hoạt chủ đề trong năm",
            "tieu_van": "lớp hạn năm theo quy tắc Tiểu vận",
            "luu_nguyet": "kích hoạt theo tháng Tiết khí",
            "luu_nhat": "vi mô theo ngày",
            "luu_thoi": "vi mô theo giờ",
        },
        "anti_error_rules": [
            "Không gọi Giáp Cung là Nhị Hợp.",
            "Không gọi Xung Chiếu là Tam Hợp.",
            "Không chọn Quan/Tài/Tật/Di theo tên chức năng thay cho cung thực tế.",
        ],
    }
