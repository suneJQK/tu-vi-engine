"""V2 chart builder facade over the existing deterministic local engine."""
from __future__ import annotations

from typing import Any

from ..schema import require_valid_v2_chart, to_v2_chart
from .date_handler import normalize_birth_input
from .serializer import serialize_palace


def _lap_la_so_uncached(
    day: int,
    month: int,
    year: int,
    hour: int,
    gender: int,
    name: str = "",
    is_solar: bool = True,
    timezone: float = 7.0,
) -> dict[str, Any]:
    from tuvi_engine._engine import diaBan, lapDiaBan, lapThienBan

    db = lapDiaBan(diaBan, day, month, year, hour, gender, is_solar, timezone)
    tb = lapThienBan(day, month, year, hour, gender, name, db, is_solar, timezone)
    cungs: dict[str, Any] = {}
    for index in range(1, 13):
        palace = serialize_palace(db.thapNhiCung[index], cung_so=index)
        key = palace["cung"] or palace["dia_chi"] or str(index)
        cungs[key] = palace

    legacy_shape = {
        "schema_version": "engine_2.1",
        "source": "local_tuvi_engine",
        "input": {
            "ngay": day,
            "thang": month,
            "nam": year,
            "gio_sinh": hour,
            "gioi_tinh": "Nam" if gender == 1 else "Nữ",
            "duong_lich": is_solar,
            "time_zone": timezone,
        },
        "thien_ban": {
            "ten": getattr(tb, "ten", name),
            "nam_nu": getattr(tb, "namNu", None),
            "gio_sinh": getattr(tb, "gioSinh", None),
            "can_nam": getattr(tb, "canNamTen", None),
            "chi_nam": getattr(tb, "chiNamTen", None),
            "can_thang": getattr(tb, "canThangTen", None),
            "chi_thang": getattr(tb, "chiThangTen", None),
            "can_ngay": getattr(tb, "canNgayTen", None),
            "chi_ngay": getattr(tb, "chiNgayTen", None),
            "menh": getattr(tb, "menh", None),
            "ban_menh": getattr(tb, "banMenh", None),
            "ten_cuc": getattr(tb, "tenCuc", None),
            "menh_chu": getattr(tb, "menhChu", None),
            "than_chu": getattr(tb, "thanChu", None),
            "am_duong_menh": getattr(tb, "amDuongMenh", None),
            "sinh_khac": getattr(tb, "sinhKhac", None),
        },
        "12_cung": cungs,
    }
    return to_v2_chart(legacy_shape)


def lap_la_so(
    ngay: int,
    thang: int,
    nam: int,
    gio_sinh: str | int,
    gioi_tinh: str | int,
    ten: str = "",
    duong_lich: bool = True,
    time_zone: float = 7.0,
) -> dict[str, Any]:
    normalized = normalize_birth_input(
        ngay, thang, nam, gio_sinh, gioi_tinh, ten, duong_lich, time_zone
    )
    from .cache import cached_lap_la_so

    chart = cached_lap_la_so(
        normalized.day,
        normalized.month,
        normalized.year,
        normalized.hour,
        normalized.gender,
        normalized.name,
        normalized.is_solar,
        normalized.timezone,
    )
    return require_valid_v2_chart(chart)
