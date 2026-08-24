"""Tính Tiểu hạn/Tiểu vận theo Tam hợp năm sinh và chiều Nam/Nữ.

Quy tắc authoritative của hệ thống:
- Thân – Tý – Thìn: khởi tại Tuất.
- Dần – Ngọ – Tuất: khởi tại Thìn.
- Tỵ – Dậu – Sửu: khởi tại Mùi.
- Hợi – Mão – Mùi: khởi tại Sửu.
- Nam: đếm thuận.
- Nữ: đếm nghịch.
- Cung khởi được đặt là Tý.
- Từ mốc Tý đó đếm đến Chi của năm xem theo chiều Nam/Nữ.
- Cung thực tế nơi Chi năm xem dừng lại là cung Tiểu hạn/Tiểu vận.

Ví dụ Hợi sinh thuộc nhóm Hợi – Mão – Mùi, cung khởi là Sửu.
Quy ước Sửu = Tý, Dần = Sửu, Mão = Dần, ... .
Năm xem có Chi Ngọ thì nam đi thuận sẽ dừng tại Mùi.

Không dùng tuổi mụ để quyết định vị trí Tiểu hạn; tuổi chỉ giữ để hiển thị/đối chiếu.
Không hard-code kết quả của một năm cụ thể.
"""
from __future__ import annotations

from typing import Any, Callable

BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

START_BRANCH_BY_BIRTH_BRANCH = {
    "Tý": "Tuất", "Thìn": "Tuất", "Thân": "Tuất",
    "Tỵ": "Mùi", "Dậu": "Mùi", "Sửu": "Mùi",
    "Dần": "Thìn", "Ngọ": "Thìn", "Tuất": "Thìn",
    "Hợi": "Sửu", "Mão": "Sửu", "Mùi": "Sửu",
}


def check(value: int) -> int:
    return (int(value) - 1) % 12 + 1


def branch_number(name: str) -> int:
    try:
        return BRANCHES.index(name) + 1
    except ValueError as exc:
        raise ValueError(f"Địa Chi không hợp lệ: {name!r}") from exc


def chi_name(value: int) -> str:
    return BRANCHES[check(value) - 1]


def _gender_direction(gender: str) -> tuple[int, str]:
    normalized = str(gender).strip().casefold()
    if normalized in {"nam", "male", "m", "1"}:
        return 1, "thuận"
    if normalized in {"nữ", "nu", "female", "f", "0", "2"}:
        return -1, "nghịch"
    raise ValueError(f"Giới tính không hợp lệ để tính Tiểu hạn: {gender!r}")


def build_tieu_van_source_mapping(
    check_fn: Callable[[int], int],
    chi_name_fn: Callable[[int], str],
    birth_branch: int,
    target_branch: int,
    gender: str,
    age: int | None = None,
) -> dict[str, Any]:
    """Tính vị trí Tiểu hạn theo cung khởi -> mốc Tý -> Chi năm xem."""
    birth_branch = check_fn(birth_branch)
    target_branch = check_fn(target_branch)

    birth_name = chi_name_fn(birth_branch)
    target_name = chi_name_fn(target_branch)
    start_branch_name = START_BRANCH_BY_BIRTH_BRANCH.get(birth_name)
    if start_branch_name is None:
        raise ValueError(f"Không xác định được cung khởi Tiểu hạn cho Chi sinh {birth_name!r}")

    direction, direction_name = _gender_direction(gender)
    start_branch = branch_number(start_branch_name)

    target_steps_from_ti = (target_branch - 1) % 12
    palace_branch = check_fn(start_branch + direction * target_steps_from_ti)
    palace_branch_name = chi_name_fn(palace_branch)

    sequence: list[dict[str, Any]] = []
    for step in range(12):
        mapped_year_branch = check_fn(1 + direction * step)
        palace_at_step = check_fn(start_branch + direction * step)
        sequence.append({
            "thu_tu": step + 1,
            "buoc_tu_ti": step,
            "chi_nam": mapped_year_branch,
            "chi_nam_ten": chi_name_fn(mapped_year_branch),
            "cung_dia_chi": palace_at_step,
            "cung_dia_chi_ten": chi_name_fn(palace_at_step),
        })

    return {
        "cung_dia_chi": palace_branch,
        "cung_dia_chi_ten": palace_branch_name,
        "cung_so": palace_branch,
        "chi_nam": target_branch,
        # For display/compatibility, chi_ten is the Địa Chi of the actual
        # Tiểu vận palace, not the Chi of the year being queried.
        "chi_ten": palace_branch_name,
        "chi_nam_sinh": birth_branch,
        "chi_nam_sinh_ten": birth_name,
        "khoang_cach_chi": target_steps_from_ti,
        "tuoi": max(1, int(age)) if age is not None else target_steps_from_ti + 1,
        "huong": direction_name,
        "cung_khoi": start_branch,
        "cung_khoi_ten": start_branch_name,
        "cung_khoi_dat_lam_ti": True,
        "tam_hop_nam_sinh": [k for k, v in START_BRANCH_BY_BIRTH_BRANCH.items() if v == start_branch_name],
        "phuong_phap": (
            "Tra cung khởi theo Tam hợp Chi năm sinh; đặt cung khởi làm Tý; "
            "Nam đếm thuận, Nữ đếm nghịch từ Tý đến Chi năm xem; "
            "cung thực tế nơi Chi năm xem dừng lại là cung Tiểu hạn"
        ),
        "source_formula": {
            "cung_khoi": "tra theo Tam hợp Chi năm sinh",
            "moc_dem": "cung_khoi = Tý",
            "so_buoc": "index(Chi_nam_xem) với Tý=0",
            "vi_tri_tieu_han": "check(cung_khoi + direction * index(Chi_nam_xem))",
            "direction": "Nam = +1 (thuận); Nữ = -1 (nghịch)",
        },
        "sequence": sequence,
    }
