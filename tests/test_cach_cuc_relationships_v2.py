from tuvi_engine.rules.evaluator import evaluate_condition, related_palaces


def _palace(no, name, chi, stars):
    return {
        "cung_so": no,
        "cung": name,
        "cung_ten": name,
        "dia_chi": chi,
        "sao": [{"name": s} for s in stars],
    }


def _chart():
    names = [
        (1, "Mệnh", "Tý"), (2, "Huynh Đệ", "Sửu"), (3, "Phu Thê", "Dần"),
        (4, "Tử Tức", "Mão"), (5, "Tài Bạch", "Thìn"), (6, "Tật Ách", "Tỵ"),
        (7, "Thiên Di", "Ngọ"), (8, "Nô Bộc", "Mùi"), (9, "Quan Lộc", "Thân"),
        (10, "Điền Trạch", "Dậu"), (11, "Phúc Đức", "Tuất"), (12, "Phụ Mẫu", "Hợi"),
    ]
    return {"12_cung": {name: _palace(no, name, chi, []) for no, name, chi in names}}


def test_tam_phuong_tu_chinh_requires_stars_in_four_house_scope():
    chart = _chart()
    chart["12_cung"]["Mệnh"]["sao"] = [{"name": "Hóa Lộc"}]
    chart["12_cung"]["Tài Bạch"]["sao"] = [{"name": "Hóa Quyền"}]
    chart["12_cung"]["Thiên Di"]["sao"] = [{"name": "Hóa Khoa"}]
    condition = {
        "tam_phuong_tu_chinh": {
            "stars_required": ["Hóa Lộc", "Hóa Quyền", "Hóa Khoa"],
            "min_count": 3,
        }
    }
    assert evaluate_condition(chart, condition) is True


def test_tam_phuong_scope_does_not_match_outside_four_house_scope():
    chart = _chart()
    chart["12_cung"]["Mệnh"]["sao"] = [{"name": "Hóa Lộc"}]
    chart["12_cung"]["Phu Thê"]["sao"] = [{"name": "Hóa Quyền"}]
    chart["12_cung"]["Tử Tức"]["sao"] = [{"name": "Hóa Khoa"}]
    condition = {
        "tam_phuong_tu_chinh": {
            "stars_required": ["Hóa Lộc", "Hóa Quyền", "Hóa Khoa"],
            "min_count": 3,
        }
    }
    assert evaluate_condition(chart, condition) is False


def test_giap_cung_pairs_require_one_star_on_each_side():
    chart = _chart()
    chart["12_cung"]["Huynh Đệ"]["sao"] = [{"name": "Tả Phù"}]
    chart["12_cung"]["Phụ Mẫu"]["sao"] = [{"name": "Hữu Bật"}]
    condition = {
        "giap_cung_pairs": [["Tả Phù", "Hữu Bật"]]
    }
    assert evaluate_condition(chart, condition) is True


def test_related_palaces_contains_all_expected_relationships():
    chart = _chart()
    target = chart["12_cung"]["Mệnh"]
    rel = related_palaces(chart, target)
    assert len(rel["tam_phuong_tu_chinh"]) == 4
    assert len(rel["tam_hop"]) == 2
    assert len(rel["xung_chieu"]) == 1
    assert len(rel["giap_cung"]) == 2
    assert len(rel["nhi_hop"]) == 1
