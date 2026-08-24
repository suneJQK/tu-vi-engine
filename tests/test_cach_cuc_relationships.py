from tuvi_engine.rules.evaluator import evaluate_condition


def _palace(no, name, branch, stars):
    return {
        "cung_so": no,
        "cung_ten": name,
        "cung": name,
        "dia_chi": branch,
        "sao": [{"ten": star} for star in stars],
    }


def _chart(palaces):
    return {"12_cung": {p["cung_ten"]: p for p in palaces}}


def test_tam_phuong_tu_chinh_requires_stars_in_scope():
    chart = _chart([
        _palace(1, "Mệnh", "Tý", ["Tử Vi"]),
        _palace(5, "Tài Bạch", "Thìn", ["Hóa Lộc"]),
        _palace(9, "Quan Lộc", "Thân", ["Hóa Quyền"]),
        _palace(7, "Thiên Di", "Ngọ", ["Hóa Khoa"]),
    ])
    assert evaluate_condition(
        chart,
        {
            "target": "Mệnh",
            "tam_phuong_tu_chinh": {
                "stars_required": ["Hóa Lộc", "Hóa Quyền", "Hóa Khoa"],
                "min_count": 3,
            },
        },
    )


def test_tam_phuong_tu_chinh_does_not_accept_unrelated_palace():
    chart = _chart([
        _palace(1, "Mệnh", "Tý", ["Tử Vi"]),
        _palace(5, "Tài Bạch", "Thìn", ["Hóa Lộc"]),
        _palace(9, "Quan Lộc", "Thân", ["Hóa Quyền"]),
        _palace(4, "Phụ Mẫu", "Mão", ["Hóa Khoa"]),
    ])
    assert not evaluate_condition(
        chart,
        {
            "target": "Mệnh",
            "tam_phuong_tu_chinh": {
                "stars_required": ["Hóa Lộc", "Hóa Quyền", "Hóa Khoa"],
                "min_count": 3,
            },
        },
    )


def test_xung_chieu_can_be_used_as_scope():
    chart = _chart([
        _palace(1, "Mệnh", "Tý", ["Cự Môn"]),
        _palace(7, "Thiên Di", "Ngọ", ["Hóa Lộc"]),
    ])
    assert evaluate_condition(
        chart,
        {
            "target": "Mệnh",
            "xung_chieu": {"stars_required": ["Hóa Lộc"]},
        },
    )
