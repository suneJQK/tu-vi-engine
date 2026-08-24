"""Minimal local compatibility layer for AmDuong.py.

The standalone engine keeps calendar calculations in tuvi_engine._engine.Lich_HND.
This module preserves the original VnCalendarUtil import path without bringing
any MCP/vendor package into the new source tree.
"""

from ..._engine.Lich_HND import (
    jdFromDate,
    S2L as _s2l,
    L2S as _l2s,
)


def solar_to_lunar_vn(dd, mm, yy, time_zone=7):
    return _s2l(dd, mm, yy, timeZone=time_zone)


def lunar_to_solar_vn(lunar_d, lunar_m, lunar_y, lunar_leap, time_zone=7):
    return _l2s(lunar_d, lunar_m, lunar_y, lunar_leap, tZ=time_zone)
