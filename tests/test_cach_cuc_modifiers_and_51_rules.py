from tuvi_engine.rules.cach_cuc import detect_cach_cuc
from tuvi_engine.rules.modifiers import detect_cach_cuc_modifiers


def _star(name: str, attr: str = "Miếu địa"):
    return {"ten": name, "dac_tinh": attr}


def _chart(menh_stars=None, quan_stars=None, menh_branch="Hợi", quan_branch="Mão"):
    names = [
        ("Mệnh", 1, menh_branch, menh_stars or []),
        ("Phụ Mẫu", 2, "Tý", []),
        ("Phúc Đức", 3, "Sửu", []),
        ("Điền Trạch", 4, "Dần", []),
        ("Quan Lộc", 5, quan_branch, quan_stars or []),
        ("Nô Bộc", 6, "Thìn", []),
        ("Thiên Di", 7, "Tỵ", []),
        ("Tật Ách", 8, "Ngọ", []),
        ("Tài Bạch", 9, "Mùi", []),
        ("Tử Tức", 10, "Thân", []),
        ("Phu Thê", 11, "Dậu", []),
        ("Huynh Đệ", 12, "Tuất", []),
    ]
    return {
        "thien_ban": {"can_nam": "Tân"},
        "12_cung": {
            name: {
                "cung_so": so,
                "cung": "Mệnh · Thân cư" if name == "Mệnh" else name,
                "dia_chi": chi,
                "sao": [_star(x) for x in stars],
            }
            for name, so, chi, stars in names
        },
    }


def test_quyen_loc_matches_and_khong_kiep_does_not_create_phung_khong():
    chart = _chart(
        menh_stars=["Thiên Đồng", "Địa Không", "Địa Kiếp", "Hóa Lộc"],
        quan_stars=["Thiên Cơ", "Cự Môn", "Hóa Quyền"],
    )
    names = {item["name"] for item in detect_cach_cuc(chart)}
    assert "Quyền Lộc Tuần Phùng Cách" in names
    assert "Mệnh Lý Phùng Không Cách" not in names


def test_loc_phung_xung_pha_reports_breaking_factor_but_keeps_core_loc():
    chart = _chart(
        menh_stars=["Hóa Lộc"],
        quan_stars=["Hóa Quyền"],
    )
    # Xung Chiếu of Mệnh Hợi is Tỵ; put Hóa Kỵ there.
    chart["12_cung"]["Thiên Di"]["sao"] = [_star("Hóa Kỵ")]
    modifiers = detect_cach_cuc_modifiers(chart)
    assert any(m["id"] == "loc_phung_xung_pha" for m in modifiers)
    hit = next(m for m in modifiers if m["id"] == "loc_phung_xung_pha")
    assert any(e["star"] == "Hóa Kỵ" and e["relation"] == "xung_chieu" for e in hit["breaking_evidence"])


def test_quyen_loc_without_breaker_has_no_loc_modifier():
    chart = _chart(
        menh_stars=["Hóa Lộc"],
        quan_stars=["Hóa Quyền"],
    )
    assert detect_cach_cuc_modifiers(chart) == []
