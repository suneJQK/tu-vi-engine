from tuvi_engine.van_tieu_van_patch import build_tieu_van_source_mapping


BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


def check(value: int) -> int:
    return (int(value) - 1) % 12 + 1


def chi_name(value: int) -> str:
    return BRANCHES[check(value) - 1]


def calc(birth: str, target: str, gender: str):
    return build_tieu_van_source_mapping(
        check,
        chi_name,
        BRANCHES.index(birth) + 1,
        BRANCHES.index(target) + 1,
        gender,
    )


def test_than_ty_thin_male_follows_forward():
    # Tý thuộc Thân–Tý–Thìn -> khởi Tuất.
    # Tý -> Tuất, Sửu -> Hợi, ..., Ngọ -> Thìn.
    result = calc("Tý", "Ngọ", "Nam")
    assert result["cung_khoi_ten"] == "Tuất"
    assert result["cung_dia_chi_ten"] == "Thìn"
    assert result["huong"] == "thuận"


def test_than_ty_thin_female_goes_reverse():
    result = calc("Tý", "Ngọ", "Nữ")
    assert result["cung_khoi_ten"] == "Tuất"
    assert result["cung_dia_chi_ten"] == "Thìn"
    assert result["huong"] == "nghịch"


def test_ty_dau_suu_male_and_female():
    # Dậu thuộc Tỵ–Dậu–Sửu -> khởi Mùi.
    male = calc("Dậu", "Tý", "Nam")
    female = calc("Dậu", "Tý", "Nữ")
    assert male["cung_khoi_ten"] == "Mùi"
    assert male["cung_dia_chi_ten"] == "Mùi"
    assert male["huong"] == "thuận"
    assert female["cung_khoi_ten"] == "Mùi"
    assert female["cung_dia_chi_ten"] == "Mùi"
    assert female["huong"] == "nghịch"


def test_dan_ngo_tuat_male_and_female():
    # Ngọ thuộc Dần–Ngọ–Tuất -> khởi Thìn.
    male = calc("Ngọ", "Hợi", "Nam")
    female = calc("Ngọ", "Hợi", "Nữ")
    assert male["cung_khoi_ten"] == "Thìn"
    assert male["cung_dia_chi_ten"] == "Mão"
    assert male["huong"] == "thuận"
    # Từ mốc Tý lùi 11 bước: Thìn -> Tuất.
    assert female["cung_khoi_ten"] == "Thìn"
    assert female["cung_dia_chi_ten"] == "Tuất"
    assert female["huong"] == "nghịch"


def test_hoi_mao_mui_male_and_female():
    # Mão thuộc Hợi–Mão–Mùi -> khởi Sửu.
    male = calc("Mão", "Tuất", "Nam")
    female = calc("Mão", "Tuất", "Nữ")
    assert male["cung_khoi_ten"] == "Sửu"
    assert male["cung_dia_chi_ten"] == "Hợi"
    assert male["huong"] == "thuận"
    assert female["cung_khoi_ten"] == "Sửu"
    assert female["cung_dia_chi_ten"] == "Tỵ"
    assert female["huong"] == "nghịch"


def test_same_birth_chart_changes_with_viewing_year():
    # Cùng Bính Tý nam nhưng khác năm xem => cung Tiểu hạn thay đổi.
    age_30 = build_tieu_van_source_mapping(check, chi_name, 1, 6, "Nam", age=30)
    age_31 = build_tieu_van_source_mapping(check, chi_name, 1, 7, "Nam", age=31)
    assert age_30["cung_dia_chi_ten"] == "Mão"
    assert age_31["cung_dia_chi_ten"] == "Thìn"
    assert age_30["cung_dia_chi_ten"] != age_31["cung_dia_chi_ten"]


def test_all_birth_groups_have_expected_start_branch():
    expected = {
        "Tý": "Tuất", "Thìn": "Tuất", "Thân": "Tuất",
        "Tỵ": "Mùi", "Dậu": "Mùi", "Sửu": "Mùi",
        "Dần": "Thìn", "Ngọ": "Thìn", "Tuất": "Thìn",
        "Hợi": "Sửu", "Mão": "Sửu", "Mùi": "Sửu",
    }
    expected_palaces = {"Tý": "Tuất", "Sửu": "Thân", "Dần": "Ngọ", "Mão": "Thìn", "Thìn": "Dần", "Tỵ": "Tý", "Ngọ": "Tuất", "Mùi": "Thân", "Thân": "Ngọ", "Dậu": "Thìn", "Tuất": "Dần", "Hợi": "Tý"}
    for branch_name, start_name in expected.items():
        result = calc(branch_name, branch_name, "Nam")
        assert result["cung_khoi_ten"] == start_name
        assert result["cung_dia_chi_ten"] == expected_palaces[branch_name]


def test_invalid_gender_is_rejected():
    try:
        calc("Tý", "Ngọ", "X")
    except ValueError as exc:
        assert "Giới tính không hợp lệ" in str(exc)
    else:
        raise AssertionError("Expected invalid gender to raise ValueError")
