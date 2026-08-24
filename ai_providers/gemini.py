from __future__ import annotations

import os
import random
import threading
import time


_KEY_LOCK = threading.Lock()
_KEY_COOLDOWN_UNTIL: dict[str, float] = {}
_KEY_INDEX = 0


def _is_transient_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "503",
            "unavailable",
            "high demand",
            "429",
            "resource exhausted",
            "rate limit",
            "temporarily",
        )
    )


def _gemini_keys() -> list[str]:
    keys: list[str] = []
    # New pool: GEMINI_API_KEY_1 ... GEMINI_API_KEY_20
    for index in range(1, 21):
        value = os.environ.get(f"GEMINI_API_KEY_{index}", "").strip()
        if value and value not in keys:
            keys.append(value)
    # Backward-compatible single key.
    legacy = os.environ.get("GEMINI_API_KEY", "").strip()
    if legacy and legacy not in keys:
        keys.append(legacy)
    return keys


def _select_key(keys: list[str]) -> str:
    global _KEY_INDEX
    now = time.monotonic()
    with _KEY_LOCK:
        available = [
            key for key in keys if _KEY_COOLDOWN_UNTIL.get(key, 0.0) <= now
        ]
        if not available:
            # Nếu tất cả key đang cooldown, dùng key có cooldown gần hết nhất.
            available = sorted(keys, key=lambda key: _KEY_COOLDOWN_UNTIL.get(key, 0.0))[:1]
        key = available[_KEY_INDEX % len(available)]
        _KEY_INDEX += 1
        return key


def _cooldown_key(key: str, seconds: float) -> None:
    with _KEY_LOCK:
        _KEY_COOLDOWN_UNTIL[key] = max(
            _KEY_COOLDOWN_UNTIL.get(key, 0.0),
            time.monotonic() + seconds,
        )


def generate(*, system_instruction: str, prompt: str) -> str:
    keys = _gemini_keys()
    if not keys:
        raise RuntimeError(
            "Thiếu Gemini API key. Hãy cấu hình GEMINI_API_KEY_1, "
            "GEMINI_API_KEY_2, ... trên Vercel Environment Variables."
        )

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        raise RuntimeError(f"Thiếu thư viện Gemini: {type(exc).__name__}: {exc}") from exc

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
        max_output_tokens=30000,
    )
    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    # Tối đa một vòng qua toàn bộ key pool + retry ngắn cho từng key.
    tried: set[str] = set()
    last_error: Exception | None = None

    for _ in range(len(keys)):
        key = _select_key(keys)
        if key in tried:
            continue
        tried.add(key)
        client = genai.Client(api_key=key)

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                text = getattr(response, "text", None)
                if not text:
                    raise RuntimeError("Gemini không trả về nội dung")
                return text
            except Exception as exc:
                last_error = exc
                if not _is_transient_error(exc):
                    raise
                # Key hiện tại có dấu hiệu throttling/quota tạm thời.
                _cooldown_key(key, min(60.0, 2.0 ** (attempt + 1)))
                if attempt >= 2:
                    break
                time.sleep((1.0 * (2 ** attempt)) + random.uniform(0.0, 0.4))

    raise RuntimeError(
        f"Tất cả Gemini API key hiện không khả dụng sau khi retry/rotation: {last_error}"
    ) from last_error
