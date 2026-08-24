from __future__ import annotations

import json
import os


def _extract_output(payload: dict) -> str:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    parts: list[str] = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            value = content.get("text")
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
    return "\n".join(parts).strip()


def generate(*, system_instruction: str, prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Thiếu OPENAI_API_KEY")

    model = os.environ.get("OPENAI_MODEL", "gpt-5.6").strip()
    timeout_seconds = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "90"))

    try:
        import httpx
    except Exception as exc:
        raise RuntimeError(f"Thiếu httpx: {type(exc).__name__}: {exc}") from exc

    payload = {
        "model": model,
        "instructions": system_instruction,
        "input": prompt,
    }

    try:
        with httpx.Client(
            timeout=httpx.Timeout(timeout_seconds, connect=20.0),
            trust_env=False,
            follow_redirects=True,
        ) as client:
            response = client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.RequestError as exc:
        raise RuntimeError(
            "Không kết nối được OpenAI API. "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            error_body = response.json()
            message = error_body.get("error", {}).get("message") or json.dumps(
                error_body, ensure_ascii=False
            )
            code = error_body.get("error", {}).get("code")
            error_type = error_body.get("error", {}).get("type")
        except Exception:
            message = response.text[:2000]
            code = None
            error_type = None

        details = [f"HTTP {response.status_code}: {message}"]
        if error_type:
            details.append(f"type={error_type}")
        if code:
            details.append(f"code={code}")
        raise RuntimeError("OpenAI API lỗi — " + "; ".join(details))

    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(
            f"OpenAI trả về dữ liệu không hợp lệ: {type(exc).__name__}: {exc}"
        ) from exc

    text = _extract_output(data)
    if not text:
        raise RuntimeError("OpenAI không trả về nội dung luận giải")
    return text
