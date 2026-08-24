"""Small deterministic cache around the local chart engine."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any


def _key(
    day: int,
    month: int,
    year: int,
    hour: int,
    gender: int,
    name: str,
    is_solar: bool,
    timezone: float,
) -> tuple[Any, ...]:
    return (
        int(day), int(month), int(year), int(hour), int(gender), str(name or ""),
        bool(is_solar), round(float(timezone), 6),
    )


@lru_cache(maxsize=512)
def _cached(*args: Any) -> dict[str, Any]:
    from .chart_builder import _lap_la_so_uncached
    return _lap_la_so_uncached(*args)


def cached_lap_la_so(
    day: int,
    month: int,
    year: int,
    hour: int,
    gender: int,
    name: str = "",
    is_solar: bool = True,
    timezone: float = 7.0,
) -> dict[str, Any]:
    """Return a cached chart without exposing mutable cached state."""
    return deepcopy(_cached(*_key(day, month, year, hour, gender, name, is_solar, timezone)))


def clear_chart_cache() -> None:
    """Clear all cached chart results."""
    _cached.cache_clear()


def chart_cache_info() -> Any:
    """Expose standard functools cache statistics for diagnostics."""
    return _cached.cache_info()
