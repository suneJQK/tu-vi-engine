"""Public validation helpers for the V2 chart API."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .date_handler import BirthInput, normalize_birth_input


def validate_birth_input(
    day: int,
    month: int,
    year: int,
    hour: Any,
    gender: Any,
    name: str = "",
    is_solar: bool = True,
    timezone: float = 7.0,
) -> dict[str, Any]:
    """Return a stable validation result instead of leaking parser exceptions."""
    try:
        value = normalize_birth_input(
            day, month, year, hour, gender, name, is_solar, timezone
        )
    except ValueError as exc:
        return {"valid": False, "code": "INVALID_BIRTH_INPUT", "message": str(exc)}
    return {"valid": True, "code": None, "message": None, "data": asdict(value)}


def require_valid_birth_input(
    day: int,
    month: int,
    year: int,
    hour: Any,
    gender: Any,
    name: str = "",
    is_solar: bool = True,
    timezone: float = 7.0,
) -> BirthInput:
    """Validate input and raise a ValueError with the stable error code prefix."""
    result = validate_birth_input(day, month, year, hour, gender, name, is_solar, timezone)
    if not result["valid"]:
        raise ValueError(f'{result["code"]}: {result["message"]}')
    return BirthInput(**result["data"])
