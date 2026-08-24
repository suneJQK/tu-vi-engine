"""High-level V2 rule orchestration with mandatory Cách Cục reasoning."""
from __future__ import annotations

from typing import Any

from ..ai_context import build_ai_context
from .cach_cuc import detect_cach_cuc
from .modifiers import detect_cach_cuc_modifiers
from .relationships import attach_palace_relationships


def _build_cach_cuc_analysis(
    matched: list[dict[str, Any]],
    modifiers: list[dict[str, Any]],
) -> dict[str, Any]:
    analyses: list[dict[str, Any]] = []
    for item in matched:
        if not isinstance(item, dict):
            continue
        analyses.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "description": item.get("description"),
                "reason": item.get("reason"),
                "conditions": item.get("conditions", {}),
                "matched_branches": item.get("matched_branches", []),
                "interpretation": item.get("interpretation", {}),
                "ai_instruction": (
                    "Dùng Cách Cục này như một kết luận có bằng chứng. "
                    "Ưu tiên matched_branches.evidence để xác định sao nằm ở đồng cung, "
                    "Tam Phương Tứ Chính, Xung Chiếu, Nhị Hợp hoặc Giáp Cung. "
                    "Đối chiếu tiếp với Miếu/Vượng/Đắc/Bình/Hãm và Tuần/Triệt trước khi luận. "
                    "Sau khi xác nhận Cách Cục lõi, phải xét các modifier phá/giảm cấp. "
                    "Không khẳng định Cách Cục là đại cát nếu có evidence phá cách tương ứng. "
                    "Không khẳng định Cách Cục nếu điều kiện không có evidence tương ứng."
                ),
            }
        )
    return {
        "matched_count": len(analyses),
        "matched": analyses,
        "modifiers": modifiers,
        "required_in_reasoning": True,
        "evidence_first": True,
        "separate_core_from_modifiers": True,
    }


def analyze_chart(chart: dict[str, Any]) -> dict[str, Any]:
    # Quan hệ cung là dữ liệu cấu trúc. Resolve trước khi tạo AI context để
    # Nhị Hợp không còn phụ thuộc vào thứ tự ô trên giao diện hoặc suy đoán AI.
    result = attach_palace_relationships(chart)
    matched = detect_cach_cuc(result)
    modifiers = detect_cach_cuc_modifiers(result)
    result["cach_cuc"] = matched
    result["cach_cuc_modifiers"] = modifiers
    result["cach_cuc_analysis"] = _build_cach_cuc_analysis(matched, modifiers)

    tb = result.get("thien_ban") or {}
    result["luan_giai"] = {
        "menh": {
            "cung": "Mệnh",
            "chu_menh": tb.get("menh_chu") or tb.get("menh"),
            "ban_menh": tb.get("ban_menh"),
            "menh_chu": tb.get("menh_chu"),
        },
        "than": {"than_chu": tb.get("than_chu")},
        "cach_cuc": result["cach_cuc_analysis"],
        "van_han": {
            "dai_han": "Đang sử dụng dữ liệu đại vận của từng cung khi engine nguồn cung cấp.",
            "tieu_han": "Đang sử dụng dữ liệu tiểu vận của từng cung khi engine nguồn cung cấp.",
            "luu_nien": "Rule layer sẵn sàng mở rộng khi bổ sung bảng lưu niên.",
        },
    }

    ai_context = build_ai_context(result)
    ai_context["cach_cuc_analysis"] = result["cach_cuc_analysis"]
    ai_context["cach_cuc_modifiers"] = modifiers
    ai_context["reasoning_contract"]["cach_cuc_is_mandatory"] = True
    ai_context["reasoning_contract"]["cach_cuc_evidence_first"] = True
    ai_context["reasoning_contract"]["cach_cuc_modifiers_are_mandatory"] = True
    ai_context["reasoning_contract"]["nhi_hop_is_deterministic"] = True
    ai_context["reasoning_contract"]["nhi_hop_source"] = "12 Địa Chi / Lục Hợp; không được tự suy đoán từ vị trí giao diện"
    result["ai_context"] = ai_context
    return result
