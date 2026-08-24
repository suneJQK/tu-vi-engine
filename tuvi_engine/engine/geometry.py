"""Geometric 12-palace relationships used by the V2 engine."""
from __future__ import annotations

BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

LUC_HOP = {
    "Tý": "Sửu", "Sửu": "Tý", "Dần": "Hợi", "Hợi": "Dần",
    "Mão": "Tuất", "Tuất": "Mão", "Thìn": "Dậu", "Dậu": "Thìn",
    "Tỵ": "Thân", "Thân": "Tỵ", "Ngọ": "Mùi", "Mùi": "Ngọ",
}


def relation(a: str, b: str) -> str:
    """Return the principal positional relation between two địa chi."""
    if a not in BRANCHES or b not in BRANCHES:
        return "unknown"
    distance = (BRANCHES.index(b) - BRANCHES.index(a)) % 12
    if distance in (4, 8):
        return "tam_hop"
    if distance == 6:
        return "xung_chieu"
    if distance in (1, 11):
        return "nhi_hop"
    if distance in (5, 7):
        return "giap_cung"
    return "other"


def palace_relations(branch: str) -> dict[str, object]:
    if branch not in BRANCHES:
        raise ValueError(f"Địa chi không hợp lệ: {branch}")
    i = BRANCHES.index(branch)
    return {
        "xung_chieu": BRANCHES[(i + 6) % 12],
        "tam_hop": [BRANCHES[(i + 4) % 12], BRANCHES[(i + 8) % 12]],
        "nhi_hop": LUC_HOP[branch],
        "giap_cung": [BRANCHES[(i - 1) % 12], BRANCHES[(i + 1) % 12]],
    }
