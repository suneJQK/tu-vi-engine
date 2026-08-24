"""Local Tu Vi engine for generating charts without MCP/server dependencies."""
from ._engine import *
from .ai_context import build_ai_context, load_relationship_knowledge
from .engine import cached_lap_la_so, clear_chart_cache, lap_la_so
from .schema import SCHEMA_VERSION, build_meta, to_v2_chart, validate_v2_chart
from .star_registry import (
    MAIN_STAR_IDS,
    TRANG_SINH_IDS,
    TRANSFORMATION_IDS,
    canonical_star_name,
    dedupe_stars,
    has_star,
    is_main_star,
    is_transformation,
    is_trang_sinh,
    normalize_star_name,
    normalize_star_record,
    star_catalog,
    star_id,
    stars_in,
)
from .van_contract import (
    CANONICAL_LAYERS,
    DEPRECATED_ALIASES,
    canonicalize_van_layers,
    validate_van_layer_contract,
)

# Patch Tiểu vận before callers resolve calculate_van_layers.
from . import van_calculator as _van_calculator
from .van_tieu_van_patch import build_tieu_van_source_mapping
_van_calculator._tieu_van_source_mapping = lambda birth_branch, target_branch, gender: build_tieu_van_source_mapping(
    _van_calculator.check,
    _van_calculator.chi_name,
    birth_branch,
    target_branch,
    gender,
)

__all__ = [
    "lap_la_so", "cached_lap_la_so", "clear_chart_cache",
    "SCHEMA_VERSION", "build_meta", "to_v2_chart", "validate_v2_chart",
    "build_ai_context", "load_relationship_knowledge",
    "MAIN_STAR_IDS", "TRANG_SINH_IDS", "TRANSFORMATION_IDS",
    "normalize_star_name", "star_id", "canonical_star_name",
    "normalize_star_record", "dedupe_stars", "has_star", "stars_in",
    "is_main_star", "is_trang_sinh", "is_transformation", "star_catalog",
    "CANONICAL_LAYERS", "DEPRECATED_ALIASES",
    "canonicalize_van_layers", "validate_van_layer_contract",
]
