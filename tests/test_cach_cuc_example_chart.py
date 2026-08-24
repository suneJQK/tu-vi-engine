from tuvi_engine.rules.cach_cuc import detect_cach_cuc


def _star(name):
    return {"ten": name, "dac_tinh": "Miếu địa"}


def test_quyen_loc_matches_when_loc_in_menh_quyen_in_quan_loc():
    chart = {
        "thien_ban": {"can_nam": "Tân"},
        "12_cung": {
            "Mệnh": {
                "cung_so": 1,
                "cung": "Mệnh · Thân cư",
                "dia_chi": "Hợi",
                "sao": [_star("Thiên Đồng"), _star("Địa Không"), _star("Địa Kiếp"), _star("Hóa Lộc")],
            },
            "Quan Lộc": {
                "cung_so": 5,
                "cung": "Quan Lộc",
                "dia_chi": "Mão",
                "sao": [_star("Thiên Cơ"), _star("Cự Môn"), _star("Hóa Quyền")],
            },
            "Tài Bạch": {"cung_so": 9, "cung": "Tài Bạch", "dia_chi": "Mùi", "sao": []},
            "Thiên Di": {"cung_so": 7, "cung": "Thiên Di", "dia_chi": "Tỵ", "sao": []},
            "Phụ Mẫu": {"cung_so": 2, "cung": "Phụ Mẫu", "dia_chi": "Tý", "sao": []},
            "Phúc Đức": {"cung_so": 3, "cung": "Phúc Đức", "dia_chi": "Sửu", "sao": []},
            "Điền Trạch": {"cung_so": 4, "cung": "Điền Trạch", "dia_chi": "Dần", "sao": []},
            "Nô Bộc": {"cung_so": 6, "cung": "Nô Bộc", "dia_chi": "Thìn", "sao": []},
            "Tật Ách": {"cung_so": 8, "cung": "Tật Ách", "dia_chi": "Ngọ", "sao": []},
            "Tử Tức": {"cung_so": 10, "cung": "Tử Tức", "dia_chi": "Thân", "sao": []},
            "Phu Thê": {"cung_so": 11, "cung": "Phu Thê", "dia_chi": "Dậu", "sao": []},
            "Huynh Đệ": {"cung_so": 12, "cung": "Huynh Đệ", "dia_chi": "Tuất", "sao": []},
        },
    }
    matches = detect_cach_cuc(chart)
    names = {item["name"] for item in matches}
    assert "Quyền Lộc Tuần Phùng Cách" in names
    assert "Mệnh Lý Phùng Không Cách" not in names
