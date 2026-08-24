from __future__ import annotations

from tuvi_engine.data_loader import load_engine_config, load_star_registry
from tuvi_engine.engine.chart_builder import lap_la_so
from tuvi_engine.rules.analysis import analyze_chart
from tuvi_engine.schema import validate_v2_chart


def test_engine_registry():
    config = load_engine_config()
    stars = load_star_registry()
    assert config["version"] == "2.0"
    assert stars["count"] == 109
    assert len(stars["ids"]) == 109


def test_v2_chart_and_analysis():
    chart = lap_la_so(1, 1, 2000, "Tý", "Nam", "Test", True, 7)
    assert validate_v2_chart(chart) == []
    analyzed = analyze_chart(chart)
    assert "cach_cuc" in analyzed
    assert "luan_giai" in analyzed


def test_chart_has_twelve_palaces():
    chart = lap_la_so(1, 1, 2000, "Tý", "Nam")
    assert len(chart["12_cung"]) == 12
