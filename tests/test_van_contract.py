from tuvi_engine.van_contract import canonicalize_van_layers, validate_van_layer_contract


def test_canonicalize_uses_authoritative_four_layers():
    van = {
        "dai_van_10_nam": {"cung_so": 3},
        "luu_nien_dai_van_10_nam": [{"nam": 2026, "cung_so": 9}],
        "tieu_van_10_nam": [{"nam": 2026, "cung_so": 5}],
        "luu_nien_nam_10_nam": [{"nam": 2026, "cung_so": 7}],
        "luu_nien_tieu_van": {"nam": 2026, "cung_so": 99},
    }
    canonical = canonicalize_van_layers(van)
    assert canonical["dai_van"] == {"cung_so": 3}
    assert canonical["luu_nien_dai_van"] == [{"nam": 2026, "cung_so": 9}]
    assert canonical["tieu_van"] == [{"nam": 2026, "cung_so": 5}]
    assert canonical["luu_nien_nam"] == [{"nam": 2026, "cung_so": 7}]


def test_contract_reports_alias_mismatch():
    van = {
        "dai_van_10_nam": {},
        "luu_nien_dai_van_10_nam": [],
        "tieu_van_10_nam": [],
        "luu_nien_nam_10_nam": [],
        "luu_nien_tieu_van": {"wrong": True},
        "luu_nien_nam": {"right": True},
    }
    errors = validate_van_layer_contract(van)
    assert any("luu_nien_tieu_van" in e for e in errors)


def test_contract_accepts_matching_legacy_alias():
    van = {
        "dai_van_10_nam": {},
        "luu_nien_dai_van_10_nam": [],
        "tieu_van_10_nam": [],
        "luu_nien_nam_10_nam": [],
        "luu_nien_tieu_van": {"right": True},
        "luu_nien_nam": {"right": True},
        "luu_nien_tieu_van_10_nam": [],
    }
    assert validate_van_layer_contract(van) == []
