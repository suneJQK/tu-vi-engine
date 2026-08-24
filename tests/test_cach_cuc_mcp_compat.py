from tuvi_engine.rules.evaluator import (
    evaluate_condition,
    get_tam_phuong_tu_chinh,
    get_giap_cung,
    get_luc_hop_cung,
    get_cung_chi,
    match_house_condition,
)


def _star(name, attribute="Miếu địa"):
    return {"ten": name, "name": name, "attribute": attribute}


def _chart():
    branches = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
    names = ["Mệnh", "Phụ Mẫu", "Phúc Đức", "Điền Trạch", "Quan Lộc", "Nô Bộc", "Thiên Di", "Tật Ách", "Tài Bạch", "Tử Tức", "Phu Thê", "Huynh Đệ"]
    palaces = []
    for i, (branch, name) in enumerate(zip(branches, names), 1):
        palaces.append({"cung_so": i, "cung": name, "cung_ten": f"Can {branch}", "dia_chi": branch, "sao": []})
    palaces[0]["sao"] = [_star("Hóa Lộc")]
    palaces[4]["sao"] = [_star("Hóa Quyền")]
    palaces[6]["sao"] = [_star("Hóa Khoa")]
    return {"12_cung": {p["cung"]: p for p in palaces}, "thien_ban": {"can_nam": "Giáp"}}


def test_tam_phuong_tu_chinh_contains_four_houses():
    chart = _chart()
    houses = get_tam_phuong_tu_chinh(chart, 1)
    assert len(houses) == 4
    assert {p["cung_so"] for p in houses} == {1, 5, 7, 9}


def test_giap_cung_pairs_are_adjacent():
    chart = _chart()
    left, right = get_giap_cung(chart, 1)
    assert left["cung_so"] == 12
    assert right["cung_so"] == 2


def test_luc_hop_and_chi_helpers():
    chart = _chart()
    menh = chart["12_cung"]["Mệnh"]
    assert get_cung_chi(menh) == "Tý"
    assert get_luc_hop_cung(chart, 1)["cung_so"] == 2


def test_tam_phuong_alias_uses_real_four_palaces():
    chart = _chart()
    condition = {"target": "Mệnh", "tam_phuong_tu_chinh_aux": {"stars_required": ["Hóa Lộc", "Hóa Quyền", "Hóa Khoa"], "min_count": 3}}
    assert evaluate_condition(chart, condition) is True


def test_giap_pairs_require_one_star_on_each_side():
    chart = _chart()
    chart["12_cung"]["Huynh Đệ"]["sao"] = [_star("Tả Phù")]
    chart["12_cung"]["Phụ Mẫu"]["sao"] = [_star("Hữu Bật")]
    assert evaluate_condition(chart, {"target": "Mệnh", "giap_cung_pairs": [["Tả Phù", "Hữu Bật"]]}) is True


def test_single_house_predicates_remain_available():
    chart = _chart()
    menh = chart["12_cung"]["Mệnh"]
    assert match_house_condition(menh, {"stars_all": ["Hóa Lộc"]}) is True
    assert match_house_condition(menh, {"stars_none": ["Địa Không"]}) is True
