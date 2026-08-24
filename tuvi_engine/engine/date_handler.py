"""Input/date normalization and validation for the V2 engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

BRANCH_TO_INDEX = {
    "Tý": 1, "Sửu": 2, "Dần": 3, "Mão": 4, "Thìn": 5, "Tỵ": 6,
    "Tị": 6, "Ngọ": 7, "Mùi": 8, "Thân": 9, "Dậu": 10,
    "Tuất": 11, "Hợi": 12,
}

GENDER_TO_VALUE = {
    "nam": 1, "male": 1, "m": 1, "+1": 1, "1": 1,
    "nữ": -1, "nu": -1, "female": -1, "f": -1, "-1": -1, "0": -1,
}

MIN_YEAR = 1800
MAX_YEAR = 2200
MIN_TIMEZONE = -12.0
MAX_TIMEZONE = 14.0


@dataclass(frozen=True)
class BirthInput:
    day: int
    month: int
    year: int
    hour: int
    gender: int
    name: str = ""
    is_solar: bool = True
    timezone: float = 7.0


def parse_gender(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else -1
    if isinstance(value, int):
        if value in (1, -1):
            return value
        raise ValueError("gioi_tinh phải là 1/-1 hoặc Nam/Nữ")
    key = str(value).strip().casefold()
    try:
        return GENDER_TO_VALUE[key]
    except KeyError as exc:
        raise ValueError("gioi_tinh phải là Nam/Nữ hoặc 1/-1") from exc


def parse_hour_branch(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("gio_sinh không hợp lệ")
    if isinstance(value, int):
        if 1 <= value <= 12:
            return value
        raise ValueError("gio_sinh phải nằm trong 1..12")
    text = str(value).strip()
    if text.isdigit():
        return parse_hour_branch(int(text))
    try:
        return BRANCH_TO_INDEX[text]
    except KeyError as exc:
        raise ValueError("gio_sinh phải là số 1..12 hoặc tên 12 địa chi") from exc


def validate_date(day: int, month: int, year: int) -> None:
    if not MIN_YEAR <= int(year) <= MAX_YEAR:
        raise ValueError(f"Năm sinh phải nằm trong khoảng {MIN_YEAR}-{MAX_YEAR}")
    try:
        date(int(year), int(month), int(day))
    except ValueError as exc:
        raise ValueError(f"Ngày sinh không hợp lệ: {day}/{month}/{year}") from exc


def validate_timezone(timezone: float) -> float:
    try:
        value = float(timezone)
    except (TypeError, ValueError) as exc:
        raise ValueError("timezone phải là số") from exc
    if not MIN_TIMEZONE <= value <= MAX_TIMEZONE:
        raise ValueError(f"timezone phải nằm trong khoảng {MIN_TIMEZONE:g} đến {MAX_TIMEZONE:g}")
    return value


def normalize_birth_input(
    day: int,
    month: int,
    year: int,
    hour: Any,
    gender: Any,
    name: str = "",
    is_solar: bool = True,
    timezone: float = 7.0,
) -> BirthInput:
    validate_date(day, month, year)
    return BirthInput(
        day=int(day),
        month=int(month),
        year=int(year),
        hour=parse_hour_branch(hour),
        gender=parse_gender(gender),
        name=str(name or "").strip(),
        is_solar=bool(is_solar),
        timezone=validate_timezone(timezone),
    )
