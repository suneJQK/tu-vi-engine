from tuvi_engine.rules.relationships import LUC_HOP_MAP, resolve_palace_relationships


def test_luc_hop_map_is_symmetric_and_complete():
    assert len(LUC_HOP_MAP) == 12
    for branch, partner in LUC_HOP_MAP.items():
        assert LUC_HOP_MAP[partner] == branch


def test_nhi_hop_uses_dia_chi_not_dictionary_order():
    # Deliberately scrambled palace insertion order.
    cungs = {
        "Mệnh": {"cung": "Mệnh", "dia_chi": "Dần"},
        "Tài Bạch": {"cung": "Tài Bạch", "dia_chi": "Hợi"},
        "Quan Lộc": {"cung": "Quan Lộc", "dia_chi": "Ngọ"},
        "Phu Thê": {"cung": "Phu Thê", "dia_chi": "Mùi"},
    }
    relations = resolve_palace_relationships(cungs)
    assert relations["Mệnh"]["nhị_hợp"]["cung"] == "Tài Bạch"
    assert relations["Tài Bạch"]["nhị_hợp"]["cung"] == "Mệnh"
    assert relations["Quan Lộc"]["nhị_hợp"]["cung"] == "Phu Thê"
    assert relations["Phu Thê"]["nhị_hợp"]["cung"] == "Quan Lộc"


def test_nhi_hop_missing_branch_is_explicit():
    cungs = {"Mệnh": {"cung": "Mệnh", "dia_chi": "Dần"}}
    relations = resolve_palace_relationships(cungs)
    assert relations["Mệnh"]["nhị_hợp"]["dia_chi"] == "Hợi"
    assert relations["Mệnh"]["nhị_hợp"]["cung"] is None
    assert relations["Mệnh"]["status"] == "missing_partner"
