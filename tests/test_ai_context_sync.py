from tuvi_engine.ai_context import build_ai_context
from tuvi_engine.van_tieu_van_patch import build_tieu_van_source_mapping

BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


def check(value: int) -> int:
    return (int(value) - 1) % 12 + 1


def chi_name(value: int) -> str:
    return BRANCHES[check(value) - 1]


def test_ai_context_removes_static_dynamic_palace_layers():
    chart = {
        "input": {"nam": 1996, "gioi_tinh": "Nam"},
        "thien_ban": {"chi_nam": "Tý"},
        "12_cung": {
            "Nô bộc": {
                "cung_so": 5,
                "dia_chi": "Thìn",
                "tieu_van": {"cung_so": 9, "chi_ten": "Thân"},
                "dai_van": {"tuoi_bat_dau": 23},
            },
            "Tử tức": {
                "cung_so": 7,
                "dia_chi": "Ngọ",
                "tieu_van": {"cung_so": 7, "chi_ten": "Ngọ"},
            },
        },
    }
    van = {
        "year": {"nam": 2026, "chi": 7, "chi_ten": "Ngọ"},
        "age": 31,
        "tieu_van": build_tieu_van_source_mapping(
            check, chi_name, birth_branch=1, target_branch=7, gender="Nam", age=31
        ),
    }

    context = build_ai_context(chart, van=van)
    assert context["van_han"]["tieu_van"]["cung_so"] == 5
    assert context["van_han"]["tieu_van"]["chi_ten"] == "Thìn"
    for palace in context["palaces"].values():
        assert "tieu_van" not in palace
        assert "dai_van" not in palace
