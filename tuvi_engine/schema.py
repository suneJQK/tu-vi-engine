"""Canonical V2 chart schema helpers."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "2.0"
ENGINE_NAME = "luangiaibysun-v2"
SCHEMA_PATH = Path(__file__).with_name("schema_v2.json")


def build_meta(*, source: str = "local_tuvi_engine") -> dict[str, str]:
    return {
        "schema_version": SCHEMA_VERSION,
        "engine": ENGINE_NAME,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def to_v2_chart(chart: Any, *, source: str = "local_tuvi_engine") -> dict[str, Any]:
    if not isinstance(chart, dict):
        raise TypeError("chart phải là dict")
    out = deepcopy(chart)
    input_data = out.get("input")
    if not isinstance(input_data, dict):
        raise ValueError("chart thiếu trường input")
    out.pop("schema_version", None)
    out["meta"] = build_meta(source=source)
    out.setdefault("cach_cuc", [])
    out.setdefault("luan_giai", {})
    return out


def validate_v2_chart(chart: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(chart, dict):
        return ["chart phải là object"]

    meta = chart.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta phải là object")
    elif meta.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"meta.schema_version phải là {SCHEMA_VERSION}")

    for key in ("input", "thien_ban", "12_cung"):
        if key not in chart:
            errors.append(f"thiếu trường {key}")

    input_data = chart.get("input")
    if isinstance(input_data, dict):
        for key in ("ngay", "thang", "nam", "gio_sinh", "gioi_tinh", "duong_lich", "time_zone"):
            if key not in input_data:
                errors.append(f"input thiếu {key}")
        if input_data.get("gioi_tinh") not in {"Nam", "Nữ"}:
            errors.append("input.gioi_tinh phải là Nam hoặc Nữ")
        if not isinstance(input_data.get("ngay"), int) or not 1 <= input_data["ngay"] <= 31:
            errors.append("input.ngay không hợp lệ")
        if not isinstance(input_data.get("thang"), int) or not 1 <= input_data["thang"] <= 12:
            errors.append("input.thang không hợp lệ")
        if not isinstance(input_data.get("nam"), int) or not 1800 <= input_data["nam"] <= 2200:
            errors.append("input.nam phải nằm trong 1800-2200")
        if not isinstance(input_data.get("gio_sinh"), int) or not 1 <= input_data["gio_sinh"] <= 12:
            errors.append("input.gio_sinh phải nằm trong 1..12")
        if not isinstance(input_data.get("duong_lich"), bool):
            errors.append("input.duong_lich phải là boolean")
        tz = input_data.get("time_zone")
        if not isinstance(tz, (int, float)) or not -12 <= float(tz) <= 14:
            errors.append("input.time_zone phải nằm trong -12..14")
    else:
        errors.append("input phải là object")

    cungs = chart.get("12_cung")
    if not isinstance(cungs, dict):
        errors.append("12_cung phải là object")
    elif len(cungs) != 12:
        errors.append(f"12_cung phải có đúng 12 cung, hiện có {len(cungs)}")
    else:
        for name, palace in cungs.items():
            if not isinstance(palace, dict):
                errors.append(f"12_cung.{name} phải là object")
                continue
            for key in ("cung", "can_chi", "dia_chi", "chinh_tinh", "phu_tinh"):
                if key not in palace:
                    errors.append(f"12_cung.{name} thiếu {key}")
            for key in ("chinh_tinh", "phu_tinh"):
                if key in palace and not isinstance(palace[key], list):
                    errors.append(f"12_cung.{name}.{key} phải là array")

    return errors


def require_valid_v2_chart(chart: Any) -> dict[str, Any]:
    errors = validate_v2_chart(chart)
    if errors:
        raise ValueError("; ".join(errors))
    return chart
