# Changelog

## 3.0.0 — Hợp nhất frontend & audit production

### Hợp nhất
- Gộp `new-ui/`, `v3/frontend/`, `index.html` (root) thành một frontend duy nhất `web/`.
  Giữ bản `app.js` mới nhất (có `supportStars` / `trangSinhName`), `audit-ui.js` và `van10.js`.
- Gộp `system_prompt_tuvi.txt` (root) vào `system_prompts/00_core_tuvi.txt` — trước đây cả hai
  cùng được nối vào system prompt mỗi lần gọi AI.

### Gỡ dead code
- Xóa `app.py` và `ui/app_v2.py` (2 app Streamlit song song không được deploy).
- Xóa `api/main.py` (FastAPI app thứ hai, không có route nào trỏ tới) và `api/ui_theme.py`
  (import `ui_theme` — module không tồn tại trong repo).
- Xóa chuỗi OCR không được API dùng: `ocr_engine.py`, `ocr_normalizer.py`, `palace_parser.py`,
  `chart_parser.py`, `chart_validator.py`, `tu_vi_dictionary.json` và test tương ứng.
- Xóa `pdf/renderer.py` (không có caller), `tu_vi_engine.json` ở root (bản dùng thật là
  `data/tu_vi_engine.json`), `data/cach_cuc_audit.json` (không caller),
  `new-ui/fix-stars.js` (không được HTML nào nạp), `TRANSFER_NOTE.md`,
  `DEPLOY_TRIGGER_STABLE_UI.md`.
- Xóa `_inject_viewing_year_ui()` trong `api/index.py`: 90 dòng HTML/CSS/JS nhúng trong backend,
  và là no-op với frontend hiện tại (không có `#dashboard`, `#modList`, `window.lapSo`).

### Sửa lỗi
- `star_registry.star_catalog()` trả về danh sách toàn `None`
  (`normalize_star_record` nhận object `Sao`, không phải ID/dict). Nay trả đủ 109 sao.
- `_compact()` cắt chuỗi JSON giữa chừng → model nhận JSON hỏng. Nay ghi log cảnh báo,
  gắn nhãn `[TRUNCATED]` rõ ràng và nâng trần mặc định lên 400 000 ký tự (`AI_PAYLOAD_LIMIT`).

### Hiệu năng
- `data_loader`: cache đĩa bằng `lru_cache`. Trước đây mỗi request đọc lại
  `cach_cuc.json` (95 KB) 3 lần + `cach_cuc_overrides.json` 3 lần và merge lại từ đầu.
- Cache `_system_prompt()`, `_available_ai_modes()`, `_load_ai_mode()` — trước đây đọc đĩa mỗi request.
- `/api/lap-so` không trả `ai_context` nữa (frontend không đọc field này): 293 KB → 77 KB (−74%).
- `/api/luan-giai` trả `van` thay vì toàn bộ `calculation`, và bỏ `ai_context`.
- Payload gửi AI bỏ hai field trùng lặp byte-for-byte (`palaces`, `matched_cach_cuc`): −30%.

### Deploy
- `vercel.json`: thêm route tĩnh cho `/web/*` và `/data/*`, route `/ai-mode`, và SPA fallback.
  Trước đây `/data/branch_aliases.json` mà frontend fetch không có route tường minh.
- Thêm `.vercelignore` (loại `tests/`, `scripts/`, `__pycache__`, `.pytest_cache`).
- `requirements.txt`: bỏ `streamlit`, `uvicorn`, `reportlab`, `jsonschema`, `pytest`, `httpx`
  khỏi runtime — không package nào trong số này được code production import.

### Nợ kỹ thuật còn lại
- 10 test đang đỏ do kỳ vọng sai (xem `docs/AUDIT.md`), không phải lỗi engine.
