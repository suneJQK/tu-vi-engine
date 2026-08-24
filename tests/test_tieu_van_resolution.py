from tu_vi_calculator import _sync_tieu_van


def _chart():
    branches = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
    return {
        "input": {"nam": 1996, "gioi_tinh": "Nam"},
        "thien_ban": {"chi_nam": "Tý"},
        "12_cung": {
            f"Cung {i}": {
                "cung_so": i,
                "cung": f"Cung {i}",
                "dia_chi": branches[i - 1],
                "can_chi": branches[i - 1],
            }
            for i in range(1, 13)
        },
    }


def test_birth_year_default_does_not_require_branch_name_lookup():
    chart = _chart()
    van = {
        "year": {"nam": 1996, "chi": 1, "chi_ten": "Tý"},
        "age": 1,
    }
    _sync_tieu_van(chart, van)
    assert van["tieu_van"]["cung_so"] == 11
    assert van["tieu_van"]["dia_chi"] == "Tuất"


def test_2026_binh_ty_maps_to_canonical_position_5():
    chart = _chart()
    van = {
        "year": {"nam": 2026, "chi": 7, "chi_ten": "Ngọ"},
        "age": 31,
    }
    _sync_tieu_van(chart, van)
    assert van["tieu_van"]["cung_so"] == 5
    assert van["tieu_van"]["dia_chi"] == "Thìn"
