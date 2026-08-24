from tuvi_engine.star_registry import (
    MAIN_STAR_IDS,
    TRANG_SINH_IDS,
    canonical_star_name,
    has_star,
    is_main_star,
    is_transformation,
    is_trang_sinh,
    normalize_star_name,
    star_catalog,
    star_id,
)


def test_registry_exposes_all_engine_stars():
    catalog = star_catalog()
    ids = {item["id"] for item in catalog if item}
    assert len(ids) == 109
    assert ids == set(range(1, 110))


def test_star_lookup_accepts_id_name_and_dict_forms():
    assert star_id(1) == 1
    assert star_id("Tử Vi") == 1
    assert star_id({"saoID": 1}) == 1
    assert star_id({"ten": "TỬ VI"}) == 1
    assert normalize_star_name("Văn Khúc") == normalize_star_name("Văn khúc")
    assert canonical_star_name(14) == "Phá quân"


def test_star_classification_uses_registry():
    assert is_main_star(1)
    assert is_main_star("Tử vi")
    assert not is_main_star(15)
    assert is_trang_sinh(39)
    assert is_trang_sinh("Tràng sinh")
    assert is_transformation(94)
    assert not is_transformation(1)
    assert MAIN_STAR_IDS == frozenset(range(1, 15))
    assert TRANG_SINH_IDS == frozenset(range(39, 51))


def test_has_star_matches_across_chart_star_contracts():
    palace = {
        "sao": [{"saoID": 1, "saoTen": "Tử vi"}, {"id": 94, "ten": "Hóa lộc"}],
    }
    assert has_star(palace, "TỬ VI")
    assert has_star(palace, 1)
    assert has_star(palace, "Hóa Lộc")
    assert not has_star(palace, "Tham lang")
