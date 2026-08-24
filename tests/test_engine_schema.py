# -*- coding: utf-8 -*-
"""Smoke tests cho engine an sao và schema hiển thị."""
from tuvi_lap_so_engine import lap_la_so
from chart_sanitizer import normalize_engine_chart


def test_main_stars_never_appear_in_supporting_stars():
    chart = lap_la_so(11, 11, 1996, "Tý", "Nam", "", True, 7)
    for palace in chart["12_cung"].values():
        main_ids = {s["id"] for s in palace["chinh_tinh"]}
        support_ids = {s["id"] for s in palace["phu_tinh"]}
        assert main_ids.isdisjoint(support_ids)
        assert main_ids.issubset(set(range(1, 15)))


def test_key_stars_are_placed_once():
    chart = lap_la_so(11, 11, 1996, "Tý", "Nam", "", True, 7)
    all_stars = [s for p in chart["12_cung"].values() for s in p["sao"]]
    for name in ["Thiên không", "Thiên đức", "Nguyệt đức", "Thiên quan", "Thiên phúc", "Thiên giải"]:
        assert sum(s["ten"] == name for s in all_stars) == 1, name


def test_ai_chart_has_no_raw_star_bucket_or_boolean_flags():
    chart = lap_la_so(11, 11, 1996, "Tý", "Nam", "", True, 7)
    safe = normalize_engine_chart(chart, for_ai=True)
    for palace in safe["12_cung"].values():
        assert "sao" not in palace
        assert "tuan" not in palace
        assert "triet" not in palace
        assert "tuan_triet" in palace
