from __future__ import annotations

import json
import os
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["ID", "Họ tên", "Ngày sinh", "Giờ sinh", "Giới tính", "Lịch", "Múi giờ", "Thời gian tạo"]


def _google_modules():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        return Credentials, build
    except Exception as exc:
        raise RuntimeError(f"Thiếu thư viện Google Sheets: {type(exc).__name__}: {exc}") from exc


def _credentials():
    Credentials, _ = _google_modules()
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("Thiếu GOOGLE_SERVICE_ACCOUNT_JSON")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON không phải JSON hợp lệ") from exc
    if not isinstance(info, dict) or not info.get("client_email") or not info.get("private_key"):
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON thiếu client_email hoặc private_key")
    return Credentials.from_service_account_info(info, scopes=SCOPES)


def _sheet_id() -> str:
    value = os.environ.get("GOOGLE_SHEET_ID", "").strip()
    if not value:
        raise RuntimeError("Thiếu GOOGLE_SHEET_ID")
    return value


def _service():
    _, build = _google_modules()
    return build("sheets", "v4", credentials=_credentials(), cache_discovery=False)


def _text(value: Any, default: str = "—") -> str:
    text = str(value or "").strip()
    return text or default


def _birth_date_text(value: str) -> str:
    """Store the birth date as literal text, never as a Sheets date serial."""
    return _text(value)


def _normalize(value: Any) -> str:
    return str(value or "").strip().casefold()


def _profile_match(row: list[Any], *, birth_date: str, birth_time: str, gender: str, calendar: str, time_zone: str) -> bool:
    """Identify the same birth profile even when an old random/legacy ID exists."""
    if len(row) < 8:
        return False
    return (
        _normalize(row[2]) == _normalize(birth_date)
        and _normalize(row[3]) == _normalize(birth_time)
        and _normalize(row[4]) == _normalize(gender)
        and _normalize(row[5]) == _normalize(calendar)
        and _normalize(row[6]) == _normalize(time_zone)
    )


def save_user_profile(*, user_id: str, name: str, ngay_sinh: str, gio_sinh: str, gioi_tinh: str, lich: str, time_zone: float, created_at: str) -> dict[str, Any]:
    service = _service()
    spreadsheet_id = _sheet_id()
    values_api = service.spreadsheets().values()

    first = values_api.get(spreadsheetId=spreadsheet_id, range="A1:H1").execute()
    if not first.get("values"):
        values_api.update(
            spreadsheetId=spreadsheet_id,
            range="A1:H1",
            valueInputOption="RAW",
            body={"values": [HEADERS]},
        ).execute()

    stable_id = _text(user_id)
    clean_name = _text(name)
    birth_date = _birth_date_text(ngay_sinh)
    birth_time = _text(gio_sinh)
    gender = _text(gioi_tinh)
    calendar = _text(lich)
    tz = _text(time_zone)
    created = _text(created_at)
    row = [stable_id, clean_name, birth_date, birth_time, gender, calendar, tz, created]

    existing = values_api.get(spreadsheetId=spreadsheet_id, range="A2:H").execute().get("values", [])

    # First preference: exact stable ID.
    row_number = next(
        (idx + 2 for idx, values in enumerate(existing) if values and _normalize(values[0]) == _normalize(stable_id)),
        None,
    )

    # Migration fallback: find a legacy row with the same birth profile even if its ID was random.
    if row_number is None:
        row_number = next(
            (
                idx + 2
                for idx, values in enumerate(existing)
                if _profile_match(
                    values,
                    birth_date=birth_date,
                    birth_time=birth_time,
                    gender=gender,
                    calendar=calendar,
                    time_zone=tz,
                )
            ),
            None,
        )

    if row_number is not None:
        result = values_api.update(
            spreadsheetId=spreadsheet_id,
            range=f"A{row_number}:H{row_number}",
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()
        return {
            "saved": True,
            "action": "updated",
            "row": row_number,
            "profile_id": stable_id,
            "updated_range": result.get("updatedRange"),
        }

    result = values_api.append(
        spreadsheetId=spreadsheet_id,
        range="A:H",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()
    return {
        "saved": True,
        "action": "created",
        "profile_id": stable_id,
        "updated_range": result.get("updates", {}).get("updatedRange"),
    }
