from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from tuvi_lap_so_engine import lap_la_so
from tu_vi_calculator import calculate_chart
from chart_sanitizer import normalize_engine_chart
from tuvi_engine.data_loader import load_cach_cuc
from tuvi_engine.rules.analysis import analyze_chart
from ai_providers.router import generate as generate_ai, normalize_provider

ROOT = Path(__file__).resolve().parent.parent
BOOKS_FILE = ROOT / "books_cache.json"
PROMPT_DIR = ROOT / "system_prompts"
AI_MODE_DIR = ROOT / "ai_modes"
WEB_INDEX = ROOT / "index.html"
AI_MODE_INDEX = ROOT / "ai_mode.html"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app = FastAPI(title="TV AI - Tử Vi Đẩu Số", version="2.9")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Diagnostic-Token"],
)

class BirthRequest(BaseModel):
    ngay: int = Field(ge=1, le=31)
    thang: int = Field(ge=1, le=12)
    nam: int = Field(ge=1800, le=2200)
    gio_sinh: str | int
    gioi_tinh: str
    ten: str = ""
    duong_lich: bool = True
    time_zone: float = 7.0
    nam_xem: int | None = Field(default=None, ge=1800, le=2200)
    thang_xem: int | None = Field(default=None, ge=1, le=12)
    ngay_xem: int | None = Field(default=None, ge=1, le=31)
    gio_xem: int | None = Field(default=None, ge=1, le=12)

class AskRequest(BirthRequest):
    question: str = Field(min_length=1, max_length=8000)
    year: int | None = Field(default=None, ge=1800, le=2200)
    provider: str | None = None

def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default

@lru_cache(maxsize=1)
def _system_prompt() -> str:
    parts: list[str] = []
    if PROMPT_DIR.exists():
        for path in sorted(PROMPT_DIR.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts) or "Bạn là chuyên gia Tử Vi Đẩu Số."

@lru_cache(maxsize=1)
def _available_ai_modes() -> list[dict[str, str]]:
    modes: list[dict[str, str]] = []
    if not AI_MODE_DIR.exists(): return modes
    for path in sorted(AI_MODE_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        first_line = next((x.strip() for x in text.splitlines() if x.strip()), "")
        name = first_line.split(":", 1)[1].strip() if ":" in first_line else path.stem
        modes.append({"id": path.stem, "name": name, "file": path.name})
    return modes

@lru_cache(maxsize=8)
def _load_ai_mode(mode_id: str | None) -> tuple[str, str]:
    modes = _available_ai_modes()
    if not modes: return "", "standard"
    wanted = (mode_id or "standard").strip().lower()
    path = AI_MODE_DIR / f"{wanted}.txt"
    if not path.exists():
        path = AI_MODE_DIR / f"{modes[0]['id']}.txt"
        wanted = modes[0]["id"]
    return path.read_text(encoding="utf-8").strip(), wanted

AI_PAYLOAD_LIMIT = int(os.getenv("AI_PAYLOAD_LIMIT", "400000"))


def _compact(value: Any, limit: int = AI_PAYLOAD_LIMIT) -> str:
    """Serialize compactly. Truncation is reported explicitly instead of
    silently producing malformed JSON for the model."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= limit:
        return text
    logger.warning("AI payload truncated: %d/%d chars", limit, len(text))
    return text[:limit] + '\n[TRUNCATED: dữ liệu bị cắt, không suy luận trên phần thiếu]'


def _slim_ai_context(context: dict[str, Any]) -> dict[str, Any]:
    """Drop fields duplicated inside ai_payload before sending to the model.

    ``palaces`` == ``ai_payload.selected_palaces`` and
    ``matched_cach_cuc`` == ``confirmed_cach_cuc.items`` byte for byte.
    """
    payload = context.get("ai_payload")
    slim = dict(context)
    if isinstance(payload, dict) and payload.get("selected_palaces") is not None:
        slim.pop("palaces", None)
    if slim.get("matched_cach_cuc") == (slim.get("confirmed_cach_cuc") or {}).get("items"):
        slim.pop("matched_cach_cuc", None)
    return slim

def _prepare_chart(req: BirthRequest) -> dict[str, Any]:
    chart = lap_la_so(req.ngay, req.thang, req.nam, req.gio_sinh, req.gioi_tinh, req.ten, req.duong_lich, req.time_zone)
    if len(chart.get("12_cung", {})) != 12: raise ValueError("Engine không tạo đủ 12 cung")
    analyzed = analyze_chart(chart)
    analyzed.setdefault("input", {})["lich"] = "Dương lịch" if req.duong_lich else "Âm lịch"
    return normalize_engine_chart(analyzed)

def _view_year(req: BirthRequest, explicit_year: int | None = None) -> int:
    if explicit_year is not None:
        return int(explicit_year)
    if req.nam_xem is not None:
        return int(req.nam_xem)
    user_tz = timezone(timedelta(hours=float(req.time_zone)))
    return datetime.now(user_tz).year

def _view_args(req: BirthRequest, default_year: int | None = None) -> dict[str, Any]:
    return {"year": _view_year(req, default_year), "month": req.thang_xem, "day": req.ngay_xem, "hour": req.gio_xem}

def _profile_id(req: BirthRequest) -> str:
    name = req.ten.strip() or "—"
    birth_date = f"{req.ngay:02d}/{req.thang:02d}/{req.nam:04d}"
    key = "|".join([
        name.casefold(),
        birth_date,
        str(req.gio_sinh).strip().casefold(),
        req.gioi_tinh.strip().casefold(),
        "Dương lịch" if req.duong_lich else "Âm lịch",
        str(req.time_zone),
    ])
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"tvai-profile:{key}"))

def _save_profile(req: BirthRequest) -> dict[str, Any]:
    try:
        from google_sheets_storage import save_user_profile
        created_at = datetime.now(timezone.utc).astimezone(VN_TZ).isoformat(timespec="seconds")
        name = req.ten.strip() or "—"
        birth_date = f"{req.ngay:02d}/{req.thang:02d}/{req.nam:04d}"
        return save_user_profile(
            user_id=_profile_id(req),
            name=name,
            ngay_sinh=birth_date,
            gio_sinh=str(req.gio_sinh),
            gioi_tinh=req.gioi_tinh,
            lich="Dương lịch" if req.duong_lich else "Âm lịch",
            time_zone=req.time_zone,
            created_at=created_at,
        )
    except Exception as exc:
        return {"saved": False, "error": f"{type(exc).__name__}: {exc}"}

def _assert_ai_payload_sync(calc: dict[str, Any], ai_context: dict[str, Any]) -> None:
    van = calc.get("van") or {}
    authoritative = van.get("tieu_van") or {}
    synced = (van.get("sync_contract") or {}).get("tieu_van_cung_so")
    if synced != authoritative.get("cung_so"): raise ValueError("Dữ liệu Tiểu vận nội bộ không đồng bộ")
    context_van = ai_context.get("van_han") or {}
    if (context_van.get("tieu_van") or {}) != authoritative: raise ValueError("AI context và Tiểu vận authoritative không đồng bộ")
    palaces = ai_context.get("palaces") or {}
    palace_items = palaces.values() if isinstance(palaces, dict) else palaces
    forbidden = {"dai_van", "tieu_van", "luu_nien", "luu_dai_van", "luu_nguyet", "luu_nhat", "luu_thoi"}
    for palace in palace_items:
        if isinstance(palace, dict) and forbidden.intersection(palace): raise ValueError("AI context còn chứa dynamic vận tĩnh trong từng cung")

def _ai_context_for_request(chart: dict[str, Any], calc: dict[str, Any]) -> dict[str, Any]:
    context = chart.get("ai_context")
    if not isinstance(context, dict): raise ValueError("Thiếu AI context authoritative")
    _assert_ai_payload_sync(calc, context)
    return context

@app.get("/", response_class=FileResponse)
def root() -> FileResponse:
    if not WEB_INDEX.exists(): raise HTTPException(status_code=500, detail="Thiếu web/index.html")
    return FileResponse(WEB_INDEX, media_type="text/html")

@app.get("/ai-mode", response_class=FileResponse)
def ai_mode_page() -> FileResponse:
    if not AI_MODE_INDEX.exists(): raise HTTPException(status_code=500, detail="Thiếu ai_mode.html")
    return FileResponse(AI_MODE_INDEX, media_type="text/html")

@app.get("/api/health")
def health() -> dict[str, Any]: return {"status":"ok","service":"tv-ai","version":"2.9"}

@app.get("/api/ai-modes")
def ai_modes() -> dict[str, Any]: return {"modes":_available_ai_modes()}

@app.get("/api/ai-providers")
def ai_providers() -> dict[str, Any]: return {"providers":[{"id":"gemini","name":"Gemini","env_key":"GEMINI_API_KEY","model_env":"GEMINI_MODEL"},{"id":"openai","name":"ChatGPT / OpenAI","env_key":"OPENAI_API_KEY","model_env":"OPENAI_MODEL"}]}

@app.post("/api/google-sheets-test")
def google_sheets_test(request: Request) -> dict[str, Any]:
    diagnostic_token = os.getenv("DIAGNOSTIC_TOKEN")
    if not diagnostic_token or request.headers.get("X-Diagnostic-Token") != diagnostic_token:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        import google_sheets_storage as storage
        result = storage.save_user_profile(user_id="diagnostic",name="_TEST_",ngay_sinh="01/01/2000",gio_sinh="Tý",gioi_tinh="Nam",lich="Dương lịch",time_zone=7,created_at=datetime.now(timezone.utc).astimezone(VN_TZ).isoformat(timespec="seconds"))
        return {"ok":True,"result":result}
    except Exception:
        logger.exception("Google Sheets diagnostic failed")
        return {"ok":False,"error":"Diagnostic failed"}

@app.get("/api/cach-cuc")
def cach_cuc() -> dict[str, Any]:
    items = load_cach_cuc()
    return {"count": len(items), "items": items}

@app.post("/api/lap-so")
def lap_so(req: BirthRequest) -> dict[str, Any]:
    try:
        chart=_prepare_chart(req);calc=calculate_chart(chart,**_view_args(req));chart["van"]=calc.get("van",{});chart.setdefault("viewing",{})["year"]=_view_year(req);chart.setdefault("storage",{})["user_profile"]=_save_profile(req);chart.pop("ai_context",None);return chart
    except Exception as exc:
        logger.exception("Chart calculation failed")
        raise HTTPException(status_code=400, detail="Không thể lập lá số với dữ liệu đã gửi.") from exc

@app.post("/api/luan-giai")
def luan_giai(req: AskRequest, request: Request) -> dict[str, Any]:
    try:
        viewing_year=_view_year(req,req.year);req.nam_xem=viewing_year;chart=_prepare_chart(req);calc=calculate_chart(chart,**_view_args(req,viewing_year));chart["van"]=calc.get("van",{});chart.setdefault("viewing",{})["year"]=viewing_year
        context=_ai_context_for_request(chart,calc);mode_text,mode_id=_load_ai_mode(request.cookies.get("tv_ai_mode", "standard"));books=_load_json(BOOKS_FILE,[])
        payload={"question":req.question,"year":viewing_year,"mode":mode_id,"mode_prompt":mode_text,"chart_context":_slim_ai_context(context),"books":books}
        prompt=_compact(payload);system=_system_prompt();answer,selected_provider=generate_ai(provider=normalize_provider(req.provider or request.cookies.get("tv_ai_provider","gemini")),system_instruction=system,prompt=prompt)
        chart.pop("ai_context",None)
        return {"chart":chart,"van":calc.get("van",{}),"answer":answer,"ai_status":"ok","ai_mode":mode_id,"ai_provider":selected_provider,"year":viewing_year}
    except Exception as exc:
        logger.exception("AI interpretation failed")
        raise HTTPException(status_code=500, detail="Không thể hoàn tất luận giải.") from exc
