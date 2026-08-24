from tuvi_engine.data_loader import load_cach_cuc


def _rules_by_id():
    return {int(item["id"]): item for item in load_cach_cuc()}


def test_rule_count_remains_51():
    rules = _rules_by_id()
    assert len(rules) == 51
    assert set(rules) == set(range(1, 52))


def test_quyen_loc_tuan_phung_supports_dong_cung_or_hoi_chieu():
    condition = _rules_by_id()[29]["conditions"]
    assert "any_of" in condition
    assert len(condition["any_of"]) == 2
    assert condition["any_of"][0]["cung_menh"]["stars_all"] == ["Hóa Quyền", "Hóa Lộc"]
    assert condition["any_of"][1]["tam_phuong_tu_chinh"]["min_count"] == 2


def test_cu_co_dong_cung_excludes_dau():
    assert _rules_by_id()[27]["conditions"]["cung_menh"]["branches_in"] == ["Mão"]


def test_co_nguyet_dong_luong_requires_all_four():
    assert _rules_by_id()[11]["conditions"]["tam_phuong_tu_chinh"]["min_count"] == 4


def test_giap_cach_requires_distinct_adjacent_pair():
    assert _rules_by_id()[31]["conditions"]["giap_cung_pairs"] == [["Lộc Tồn", "Hóa Lộc"]]
