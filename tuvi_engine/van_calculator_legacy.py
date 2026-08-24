"""Bộ tính vận hạn theo logic nguồn tham khảo đã cung cấp.

Phân tầng:
    Lá số gốc -> Đại vận -> Lưu Đại vận -> Lưu niên/Tiểu vận
    -> Lưu nguyệt (Tiết khí) -> Lưu nhật -> Lưu thời.

Quan trọng:
- Đại vận Tử Vi dùng Cục + chiều Âm/Dương nam nữ + cung Đại vận của engine.
- Tiểu vận dùng ánh xạ Chi năm sinh -> 12 cung theo đúng đoạn nguồn.
- Lưu niên trong Đại vận dùng hàm lndv() của nguồn.
- Lưu nguyệt dùng Tiết khí/Solar Longitude, không lấy tháng âm lịch thuần túy.
- Lưu nhật dùng Julian Day để tính Can Chi ngày.
- Lưu thời dùng Can ngày + Chi giờ.
- Đại vận Tứ Trụ dùng khoảng cách đến tiết khí trước/sau, chia 3 theo tài liệu.

Giới hạn năm 1800-2200 được giữ nguyên ở API/engine hiện hữu.
"""
from __future__ import annotations

import math
from typing import Any

CAN_NAMES = ["", "Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI_NAMES = ["", "Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


def check(value: int) -> int:
    return (int(value) - 1) % 12 + 1


def check_can(value: int) -> int:
    return (int(value) - 1) % 10 + 1


def can_name(value: int) -> str:
    return CAN_NAMES[check_can(value)]


def chi_name(value: int) -> str:
    return CHI_NAMES[check(value)]


def _is_male(gender: str) -> bool:
    return str(gender).strip().casefold() in {"nam", "male", "m", "1"}


def _jd_from_date(day: int, month: int, year: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _jd_to_gregorian(jd: int) -> tuple[int, int, int]:
    if jd > 2299160:
        a = jd + 32044
        b = (4 * a + 3) // 146097
        c = a - (b * 146097) // 4
    else:
        b = 0
        c = jd + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = b * 100 + d - 4800 + m // 10
    return day, month, year


def _solar_longitude(jd: float) -> float:
    """Đúng công thức solarLongitude() trong tài liệu."""
    T = (jd - 2451545.0) / 36525.0
    T2 = T * T
    dr = math.pi / 180.0
    M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
    L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
    C = (1.914600 - 0.004817 * T - 0.000014 * T2) * math.sin(dr * M)
    C += (0.019993 - 0.000101 * T) * math.sin(dr * 2 * M)
    C += 0.000290 * math.sin(dr * 3 * M)
    theta = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = theta - 0.00569 - 0.00478 * math.sin(omega * dr)
    return lam - 360.0 * math.floor(lam / 360.0)


def tiet_khi_month(day: int, month: int, year: int, time_zone: float = 7.0) -> int:
    """Tháng Tiết khí 1..12 theo solarLongitude() + offset 315 độ của nguồn."""
    jd = _jd_from_date(day, month, year)
    local_midnight = jd - 0.5 - float(time_zone) / 24.0
    sl = _solar_longitude(local_midnight) - 315.0
    if sl < 30.0:
        sl += 360.0
    return check(int(sl // 30.0) + 1)


def can_chi_year(year: int) -> tuple[int, int]:
    return check_can(year - 1983 + 360), check(year - 1983 + 360)


def can_chi_day(day: int, month: int, year: int) -> tuple[int, int]:
    jd = _jd_from_date(day, month, year)
    return check_can(jd), check(jd + 2)


def can_chi_hour(day_can: int, hour_branch: int) -> tuple[int, int]:
    chi = check(hour_branch)
    return check_can(2 * day_can + chi - 2), chi


def _birth_year_can(chart: dict[str, Any]) -> int | None:
    raw = chart.get("thien_ban", {}).get("can_nam")
    if isinstance(raw, int):
        return check_can(raw)
    text = str(raw or "").strip()
    for idx, name in enumerate(CAN_NAMES):
        if name and text.startswith(name):
            return idx
    return None


def _birth_year_branch(chart: dict[str, Any]) -> int | None:
    raw = chart.get("thien_ban", {}).get("chi_nam")
    if isinstance(raw, int):
        return check(raw)
    text = str(raw or "").strip()
    for idx, name in enumerate(CHI_NAMES):
        if name and text.startswith(name):
            return idx
    return None


def _dv_direction(can_year: int | None, gender: str) -> int:
    """Dương Nam/Âm Nữ thuận; Âm Nam/Dương Nữ nghịch."""
    if can_year is None:
        return 1
    can_yang = check_can(can_year) % 2 == 1
    return 1 if can_yang == _is_male(gender) else -1


def _palace_by_branch(chart: dict[str, Any], branch: int) -> int | None:
    target = chi_name(branch)
    for palace in chart.get("12_cung", {}).values():
        if palace.get("dia_chi") == target:
            value = palace.get("cung_so")
            if isinstance(value, int):
                return value
    return None


def _engine_dai_van_items(chart: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for palace in chart.get("12_cung", {}).values():
        dv = palace.get("dai_van") or {}
        start = dv.get("tuoi_bat_dau")
        try:
            start_i = int(start)
        except (TypeError, ValueError):
            continue
        items.append({
            "cung_so": palace.get("cung_so"),
            "cung": palace.get("cung"),
            "dia_chi": palace.get("dia_chi"),
            "tuoi_bat_dau": start_i,
            "tuoi_ket_thuc": start_i + 9,
            "can_chi_engine": palace.get("can_chi"),
        })
    items.sort(key=lambda x: (x["tuoi_bat_dau"], x.get("cung_so") or 99))
    return items


def _tuoi_xem(birth_year: int, target_year: int) -> int:
    return target_year - birth_year + 1


def _current_dai_van(chart: dict[str, Any], target_year: int) -> dict[str, Any] | None:
    input_data = chart.get("input", {})
    birth_year = int(input_data["nam"])
    age = _tuoi_xem(birth_year, target_year)
    items = _engine_dai_van_items(chart)
    current = next((x for x in items if x["tuoi_bat_dau"] <= age <= x["tuoi_ket_thuc"]), None)
    if current is None:
        return None

    can_year = _birth_year_can(chart)
    gender = str(input_data.get("gioi_tinh", "Nam"))
    direction = _dv_direction(can_year, gender)
    cung = int(current["cung_so"])
    fl = check(cung - 2)
    yl = check_can(2 * (can_year or 1) + 1)
    dv_can = check_can(fl + yl - 1)
    dv_branch = check(cung + 10)

    return {
        **current,
        "tuoi_xem": age,
        "huong": "thuận" if direction == 1 else "nghịch",
        "can": dv_can,
        "can_ten": can_name(dv_can),
        "chi": dv_branch,
        "chi_ten": chi_name(dv_branch),
        "cung_so": cung,
        "source_formula": {"Fl": fl, "yl": yl, "can_dai_van": "checkcan(Fl + yl - 1)"},
    }


def _source_lndv(tuoi: int, cung_dai_van: int, bat_dau: int, step: int) -> int | None:
    khoi = tuoi - bat_dau
    x = cung_dai_van
    if khoi == 0:
        return x
    if khoi == 1:
        return check(x + 6)
    if khoi == 2:
        return check(x + 6 - step)
    if khoi == 3:
        return check(x + 6)
    if khoi == 4:
        return check(x + 6 + step)
    if khoi == 5:
        return check(x + 6 + 2 * step)
    if khoi == 6:
        return check(x + 6 + 3 * step)
    if khoi == 7:
        return check(x + 6 + 4 * step)
    if khoi == 8:
        return check(x + 6 + 5 * step)
    if khoi == 9:
        return check(x + 6 + 6 * step)
    return None


def _tieu_van_source_mapping(birth_branch: int, target_branch: int, gender: str) -> dict[str, Any]:
    if birth_branch in (1, 5, 9):
        i = 11
    elif birth_branch in (2, 6, 10):
        i = 8
    elif birth_branch in (3, 7, 11):
        i = 5
    else:
        i = 2

    direction = 1 if _is_male(gender) else -1
    palace = check(i + 10)
    sequence: list[dict[str, int]] = []
    for offset in range(12):
        mapped_branch = check(birth_branch + offset * direction)
        sequence.append({"cung_so": palace, "chi": mapped_branch, "thu_tu": offset + 1})
        palace = check(palace + 1)

    selected = next((x for x in sequence if x["chi"] == target_branch), None)
    return {
        "cung_so": selected["cung_so"] if selected else None,
        "chi_nam": target_branch,
        "chi_ten": chi_name(target_branch),
        "huong": "thuận" if direction == 1 else "nghịch",
        "cung_khoi": check(i + 10),
        "sequence": sequence,
    }


def _source_luu_dai_van_can(dv_can: int, cung_dv: int) -> list[dict[str, Any]]:
    i = check_can(2 * dv_can + 1)
    out = []
    for offset in range(12):
        cung = check(cung_dv + offset)
        can = check_can((offset + 1) + i - 1)
        out.append({"cung_so": cung, "can": can, "can_ten": can_name(can)})
    return out


def _tiet_khi_day_from_jd(jd: int, time_zone: float) -> int:
    day, month, year = _jd_to_gregorian(jd)
    return tiet_khi_month(day, month, year, time_zone)


def _days_to_tiet_khi(day: int, month: int, year: int, direction: int, time_zone: float) -> int:
    jd0 = _jd_from_date(day, month, year)
    current = _tiet_khi_day_from_jd(jd0, time_zone)
    for delta in range(1, 371):
        probe = jd0 + delta * direction
        if _tiet_khi_day_from_jd(probe, time_zone) != current:
            return delta
    return 0


def _tu_tru_for_date(day: int, month: int, year: int, hour_branch: int | None, time_zone: float) -> dict[str, Any]:
    year_can, year_branch = can_chi_year(year)
    tk = tiet_khi_month(day, month, year, time_zone)
    month_can = check_can(2 * year_can + tk)
    month_branch = check(tk + 2)
    day_can, day_branch = can_chi_day(day, month, year)
    result = {
        "nam": {"can": year_can, "can_ten": can_name(year_can), "chi": year_branch, "chi_ten": chi_name(year_branch)},
        "thang": {"can": month_can, "can_ten": can_name(month_can), "chi": month_branch, "chi_ten": chi_name(month_branch), "thang_tiet_khi": tk},
        "ngay": {"can": day_can, "can_ten": can_name(day_can), "chi": day_branch, "chi_ten": chi_name(day_branch)},
    }
    if hour_branch is not None:
        hour_can, hour_chi = can_chi_hour(day_can, hour_branch)
        result["gio"] = {"can": hour_can, "can_ten": can_name(hour_can), "chi": hour_chi, "chi_ten": chi_name(hour_chi)}
    return result


def _tu_tru_dai_van(chart: dict[str, Any], time_zone: float) -> dict[str, Any]:
    inp = chart.get("input", {})
    day, month, year = int(inp["ngay"]), int(inp["thang"]), int(inp["nam"])
    gender = str(inp.get("gioi_tinh", "Nam"))
    hour = inp.get("gio_sinh")
    hour_branch = int(hour) if str(hour).isdigit() else None
    birth = _tu_tru_for_date(day, month, year, hour_branch, time_zone)
    month_can = birth["thang"]["can"]
    month_chi = birth["thang"]["chi"]
    direction = 1 if _is_male(gender) else -1
    distance = _days_to_tiet_khi(day, month, year, direction, time_zone)
    age_start = (distance + 1) // 3
    if age_start < 1:
        age_start = 1

    dvs = []
    for idx in range(8):
        step = idx * direction
        can = check_can(month_can + step)
        chi = check(month_chi + step)
        dvs.append({
            "thu_tu": idx + 1,
            "tuoi_bat_dau": age_start + idx * 10,
            "tuoi_ket_thuc": age_start + idx * 10 + 9,
            "can": can,
            "can_ten": can_name(can),
            "chi": chi,
            "chi_ten": chi_name(chi),
        })

    return {
        "bon_tru_sinh": birth,
        "tuoi_nhap_van": age_start,
        "huong": "thuận" if direction == 1 else "nghịch",
        "khoang_cach_tiet_khi_ngay": distance,
        "dai_van": dvs,
        "phuong_phap_nguon": "distance_to_tiet_khi / 3",
    }


def _resolve_target_date(month: int | None, day: int | None) -> tuple[int | None, int | None]:
    if month is None:
        return None, None
    if not 1 <= month <= 12:
        raise ValueError("thang_xem phải nằm trong 1..12")
    if day is not None and not 1 <= day <= 31:
        raise ValueError("ngay_xem phải nằm trong 1..31")
    return month, day


def calculate_van_layers(
    chart: dict[str, Any],
    *,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    hour: int | None = None,
    time_zone: float | None = None,
) -> dict[str, Any]:
    inp = chart.get("input", {})
    birth_year = int(inp["nam"])
    birth_day = int(inp["ngay"])
    birth_month = int(inp["thang"])
    birth_hour = int(inp.get("gio_sinh")) if str(inp.get("gio_sinh", "")).isdigit() else None
    gender = str(inp.get("gioi_tinh", "Nam"))
    tz = float(inp.get("time_zone", 7.0) if time_zone is None else time_zone)
    target_year = birth_year if year is None else int(year)

    target_year_can, target_year_branch = can_chi_year(target_year)
    birth_can = _birth_year_can(chart)
    birth_branch = _birth_year_branch(chart)
    direction = _dv_direction(birth_can, gender)
    age = _tuoi_xem(birth_year, target_year)
    dv = _current_dai_van(chart, target_year)

    tieu_van = _tieu_van_source_mapping(birth_branch, target_year_branch, gender) if birth_branch is not None else None

    luu_nien_dv = None
    if dv is not None:
        luu_nien_dv = _source_lndv(age, int(dv["cung_so"]), int(dv["tuoi_bat_dau"]), direction)

    luu_dai_van = None
    if dv is not None:
        luu_dai_van = {
            "cung_dai_van": dv["cung_so"],
            "can_dai_van": dv["can"],
            "can_dai_van_ten": dv["can_ten"],
            "chi_dai_van": dv["chi"],
            "chi_dai_van_ten": dv["chi_ten"],
            "can_12_cung": _source_luu_dai_van_can(int(dv["can"]), int(dv["cung_so"])),
        }

    result: dict[str, Any] = {
        "algorithm_version": "source-v3.0",
        "age": age,
        "year": {
            "nam": target_year,
            "can": target_year_can,
            "can_ten": can_name(target_year_can),
            "chi": target_year_branch,
            "chi_ten": chi_name(target_year_branch),
            "cung_luu_nien": _palace_by_branch(chart, target_year_branch),
        },
        "dai_van": {"huong": "thuận" if direction == 1 else "nghịch", "dang_xet": dv, "cac_dai_van": _engine_dai_van_items(chart)},
        "luu_dai_van": luu_dai_van,
        "tieu_van": tieu_van,
        "luu_nien": {
            "cung_nam": _palace_by_branch(chart, target_year_branch),
            "chi_nam": target_year_branch,
            "chi_nam_ten": chi_name(target_year_branch),
            "cung_luu_nien_trong_dai_van": luu_nien_dv,
            "phuong_phap": "Chi năm xem + lndv() trong Đại vận hiện hành",
        },
        "tu_tru": _tu_tru_dai_van(chart, tz),
        "tu_tru_sinh": _tu_tru_for_date(birth_day, birth_month, birth_year, birth_hour, tz),
    }

    month_int, day_int = _resolve_target_date(month, day)
    if month_int is not None:
        tk = tiet_khi_month(day_int or 1, month_int, target_year, tz)
        month_can = check_can(2 * target_year_can + tk)
        month_branch = check(tk + 2)
        result["luu_nguyet"] = {
            "thang_duong": month_int,
            "ngay_moc_tinh": day_int,
            "thang_tiet_khi": tk,
            "can": month_can,
            "can_ten": can_name(month_can),
            "chi": month_branch,
            "chi_ten": chi_name(month_branch),
            "cung": _palace_by_branch(chart, month_branch),
            "is_tiet_khi_based": True,
            "phuong_phap": "solarLongitude -> thang_tk -> Can Chi tháng",
            "warning": "Nếu ngày xem nằm sát thời điểm giao tiết khí, cần giờ/phút để phân định tuyệt đối.",
        }

    if month_int is not None and day_int is not None:
        day_can, day_branch = can_chi_day(day_int, month_int, target_year)
        result["luu_nhat"] = {
            "ngay": day_int,
            "can": day_can,
            "can_ten": can_name(day_can),
            "chi": day_branch,
            "chi_ten": chi_name(day_branch),
            "cung": _palace_by_branch(chart, day_branch),
            "nhat_than_cung": _palace_by_branch(chart, day_branch),
            "phuong_phap": "Julian Day -> checkcan(jd), check(jd+2)",
        }
        if hour is not None:
            hour_can, hour_chi = can_chi_hour(day_can, int(hour))
            result["luu_thoi"] = {
                "chi": hour_chi,
                "chi_ten": chi_name(hour_chi),
                "can": hour_can,
                "can_ten": can_name(hour_can),
                "cung": _palace_by_branch(chart, hour_chi),
                "phuong_phap": "Can giờ = checkcan(2*Can ngày + Chi giờ - 2)",
            }

    result["rules_audit"] = {
        "dai_van": "Cục + chiều Âm/Dương nam nữ + tuổi nằm trong khoảng Đại vận",
        "tieu_van": "Ánh xạ Chi năm sinh/Chi năm xem theo block chitieuvan của nguồn",
        "luu_nien": "Cung theo Chi năm xem + lndv(tuoi, cung_dai_van, bat_dau, step)",
        "luu_nguyet": "Tiết khí bằng Solar Longitude; không đồng nhất tháng âm với tháng tiết khí",
        "luu_nhat": "Julian Day + Can Chi ngày",
        "luu_thoi": "Can Chi giờ từ Can ngày + Chi giờ",
        "tu_tru_dai_van": "Khoảng cách tiết khí trước/sau chia 3 để ra tuổi nhập vận",
    }
    return result
