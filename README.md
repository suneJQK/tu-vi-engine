# TV AI — Tử Vi Đẩu Số

Engine Python tất định → chuẩn hóa dữ liệu → Cách Cục có evidence → AI luận giải → Audit.

## Cấu trúc

```
api/index.py          FastAPI app duy nhất (serverless entrypoint)
web/                  Frontend duy nhất (index.html + app.js + van10.js + audit-ui.js + css)
ai_mode.html          Trang cấu hình provider/mode AI
tuvi_engine/          Engine an sao + rules + AI context
  _engine/            Lớp an sao gốc (không sửa)
  engine/             Facade V2: chart_builder, cache, serializer, validator
  rules/              cach_cuc, modifiers, relationships, evaluator
tu_vi_calculator.py   4 lớp vận hạn
chart_sanitizer.py    Chuẩn hóa chart trước khi trả ra
ai_providers/         Gemini (key pool + rotation) / OpenAI + router fallback
data/                 stars, cach_cuc, modifiers, overrides, relationships, branch aliases
system_prompts/       System prompt (nối theo thứ tự tên file)
ai_modes/             Các chế độ luận giải
tests/                pytest
```

## Nguyên tắc

1. Một frontend duy nhất: `web/`.
2. Không nhúng HTML/CSS/JS frontend vào backend.
3. Engine là nguồn authoritative; frontend chỉ hiển thị.
4. Cách Cục phải có Rule ID + Evidence.
5. Tam Hợp / Xung Chiếu / Nhị Hợp / Giáp Cung lấy từ Địa Chi, không để AI suy luận.
6. Vận hạn 10 năm lấy từ engine, không tính lại trong UI.
7. AI chỉ nhận context đã audit.

## Biến môi trường

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `GEMINI_API_KEY_1..20` | có (hoặc `GEMINI_API_KEY`) | Pool key Gemini, xoay vòng + cooldown |
| `GEMINI_MODEL` | không | Mặc định `gemini-3.6-flash` |
| `OPENAI_API_KEY` | không | Provider dự phòng |
| `OPENAI_MODEL` | không | Model OpenAI |
| `ALLOWED_ORIGINS` | không | CORS, phân tách bằng dấu phẩy. Rỗng = chỉ same-origin |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | không | Lưu hồ sơ vào Google Sheets |
| `GOOGLE_SHEET_ID` | không | ID sheet |
| `DIAGNOSTIC_TOKEN` | không | Mở endpoint `/api/google-sheets-test` |
| `AI_PAYLOAD_LIMIT` | không | Trần ký tự payload gửi AI, mặc định 400000 |

## Chạy local

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload
```

## Test

```bash
pytest -q
```
