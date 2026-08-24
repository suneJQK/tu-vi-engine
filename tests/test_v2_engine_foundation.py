import pytest

from tuvi_engine.engine.cache import cached_lap_la_so, chart_cache_info, clear_chart_cache
from tuvi_engine.engine.chart_builder import lap_la_so
from tuvi_engine.engine.date_handler import normalize_birth_input
from tuvi_engine.engine.geometry import palace_relations, relation
from tuvi_engine.schema import validate_v2_chart


def test_normalize_birth_input():
    value = normalize_birth_input(1, 1, 2000, "Tý", "Nam", timezone=7)
    assert value.hour == 1
    assert value.gender == 1


def test_validation_rejects_invalid_date_and_timezone():
    with pytest.raises(ValueError, match="Năm sinh"):
        normalize_birth_input(1, 1, 1799, "Tý", "Nam")
    with pytest.raises(ValueError, match="Ngày sinh"):
        normalize_birth_input(31, 2, 2000, "Tý", "Nam")
    with pytest.raises(ValueError, match="timezone"):
        normalize_birth_input(1, 1, 2000, "Tý", "Nam", timezone=15)


def test_geometry():
    assert relation("Tý", "Ngọ") == "xung_chieu"
    result = palace_relations("Tý")
    assert result["xung_chieu"] == "Ngọ"
    assert result["nhi_hop"] == "Sửu"


def test_lap_la_so_schema():
    chart = lap_la_so(1, 1, 2000, "Tý", "Nam", "Test", True, 7)
    assert chart["meta"]["schema_version"] == "2.0"
    assert chart["meta"]["engine"] == "luangiaibysun-v2"
    assert len(chart["12_cung"]) == 12
    assert "thien_ban" in chart
    assert validate_v2_chart(chart) == []


def test_cache_does_not_expose_mutable_state():
    clear_chart_cache()
    before = chart_cache_info().hits
    chart1 = cached_lap_la_so(1, 1, 2000, 1, 1, "Test", True, 7)
    chart1["thien_ban"]["ten"] = "MUTATED"
    chart2 = cached_lap_la_so(1, 1, 2000, 1, 1, "Test", True, 7)
    assert chart2["thien_ban"]["ten"] != "MUTATED"
    assert chart_cache_info().hits >= before + 1


def test_schema_rejects_missing_palace():
    chart = lap_la_so(1, 1, 2000, "Tý", "Nam", "Test", True, 7)
    chart["12_cung"].pop(next(iter(chart["12_cung"])))
    errors = validate_v2_chart(chart)
    assert any("đúng 12 cung" in error for error in errors)
