# Audit production-readiness

## A. Trùng lặp frontend (đã gộp)

Ba frontend cùng tồn tại, cùng gọi `/api/lap-so` + `/api/luan-giai`:

| | root `index.html` | `new-ui/` | `v3/frontend/` |
|---|---|---|---|
| Được deploy? | Không (route `/` trỏ v3) | Không | Có |
| CSS | Nhúng 7 201 ký tự | `style.css` 9 707 | Trỏ về `/new-ui/style.css` |
| JS | Nhúng 10 817 ký tự | `app.js` 18 279 | `app.js` 19 999 |

- `style.css`, `van10.css`, `van10.js` của `new-ui/` và `v3/frontend/` **giống hệt nhau** (md5 khớp).
- `index.html` của hai thư mục chỉ khác 6 dòng (đổi chữ, thêm `audit-ui.js`).
- `app.js` chỉ khác 47 dòng: bản v3 thêm `supportStars()` / `trangSinhName()` để fallback khi
  `phu_tinh` rỗng. Đây là bản mới hơn → giữ bản v3.
- Root `index.html` là bản viết lại độc lập (6/38 hàm trùng tên, 32 class CSS trùng),
  thiếu quản lý hồ sơ, streaming, TOC, audit → bỏ.
- `new-ui/fix-stars.js` monkey-patch `window.palaceHtml` với đúng logic mà v3 đã nạp thẳng vào
  `app.js`, và **không HTML nào nạp nó** → dead.

Kết quả: một thư mục `web/` duy nhất. Xóa ~34 KB frontend trùng.

## B. Dead code / file thừa

| Mục | Bằng chứng |
|---|---|
| `app.py`, `ui/app_v2.py` | 2 app Streamlit, không route nào trỏ tới, `streamlit` chỉ có trong requirements |
| `api/main.py` | FastAPI app thứ hai; `vercel.json` chỉ map `/api/*` → `api/index.py` |
| `api/ui_theme.py` | `from ui_theme import themed_index` — **module `ui_theme` không tồn tại**, import lỗi ngay |
| `ocr_engine/normalizer/palace_parser/chart_parser/chart_validator` | Chỉ được import bởi chính test của chúng; `api/index.py` không chạm |
| `pdf/renderer.py` | Không caller nào; kéo theo `reportlab` |
| `tu_vi_engine.json` (root, 21 KB) | `data_loader` đọc `data/tu_vi_engine.json` (515 B). Hai file khác nhau hoàn toàn |
| `data/cach_cuc_audit.json` | Không code nào đọc |
| `tu_vi_dictionary.json` | Chỉ `ocr_normalizer` đọc |
| `_inject_viewing_year_ui()` | 90 dòng JS/CSS nhúng trong backend; grep frontend: `#dashboard`=0, `#van10Panel`=0, `#modList`=0, `window.lapSo`=0 → toàn bộ replace là no-op |
| `TRANSFER_NOTE.md`, `DEPLOY_TRIGGER_STABLE_UI.md` | Ghi chú tạm |
| `books_cache.json` | `api/index.py` đọc nhưng file không tồn tại → luôn trả `[]`. Đã giữ nguyên code (fallback an toàn), chỉ ghi chú |

## C. Lỗi thực

### C1. `star_catalog()` trả toàn `None` — nghiêm trọng
```python
return [normalize_star_record(star) for _, star in sorted(_engine_stars().items())]
```
`_engine_stars()` trả `dict[int, Sao]`. `normalize_star_record()` chỉ nhận `int`, `str` hoặc
`dict` — với object `Sao` nó rơi vào nhánh `star_id(raw) is None` → `return None`.
Đo được: `len == 109`, `none count == 109`. Đã sửa bằng cách truyền ID.

### C2. `_compact()` gửi JSON hỏng cho AI — nghiêm trọng
Payload thực đo được 195 687 ký tự, trần cũ 90 000 → **cắt mất 54% dữ liệu** và chuỗi kết quả
không parse được JSON. Model nhận một object cụt giữa chừng mỗi lần luận giải.
Đã: nâng trần lên 400 000 (env `AI_PAYLOAD_LIMIT`), ghi log, gắn nhãn `[TRUNCATED]` rõ ràng,
và cắt bớt trùng lặp trước khi gửi.

### C3. `data/stars.json` không khớp `/stars` (đã xóa endpoint)
File có key `ids`, không có `stars`. `api/main.py` trả nguyên file → client nhận metadata,
không phải danh mục sao. Endpoint đã bị xóa cùng `api/main.py`.

## D. Hiệu năng

Đo trên pipeline `lap_la_so → analyze_chart → normalize → calculate_chart`:

| Chỉ số | Trước | Sau |
|---|---|---|
| Đọc đĩa JSON / request | 7 lần (gồm `cach_cuc.json` 95 KB × 3, merge overrides × 3) | 1 |
| Pipeline trung bình | 25,5 ms | 23,0 ms |
| Response `/api/lap-so` | 292 605 ký tự | 76 950 (−74 %) |
| Payload gửi AI | 195 588 | 137 487 (−30 %) |
| System prompt / request | Đọc 3 file đĩa mỗi lần | Cache |

Chi tiết payload AI trước tối ưu (ký tự):
`ai_payload` 98 375 · `palaces` 58 924 · `van_han` 41 379 · `confirmed_cach_cuc` 5 808 ·
`matched_cach_cuc` 5 672.
Kiểm chứng: `palaces` **bằng byte-for-byte** `ai_payload.selected_palaces`, và
`matched_cach_cuc` **bằng byte-for-byte** `confirmed_cach_cuc.items` → gửi 2 lần mỗi trường.

Hot path còn lại (profile 10 vòng): `deepcopy` chiếm 0,677 s / 1,418 s tổng.
Nguồn chính là `ai_context.build_ai_context()` — được gọi **2 lần mỗi request**
(một lần trong `analyze_chart`, một lần trong `calculate_chart`). Đây là điểm tối ưu lớn tiếp theo
nhưng cần đổi contract giữa hai module nên **chưa đụng tới** trong bản này.

## E. Cấu trúc deploy

| Vấn đề | Trạng thái |
|---|---|
| `/data/branch_aliases.json` được frontend fetch nhưng `vercel.json` không có route tĩnh | Đã thêm route `/(web\|data)/*` |
| `/ai-mode` chỉ tồn tại như route FastAPI, không có route Vercel | Đã thêm |
| Không có `.vercelignore` → `tests/`, `.pytest_cache/`, 95 file `.pyc` (768 KB) lên bundle | Đã thêm |
| `requirements.txt` cài `streamlit` + `reportlab` + `jsonschema` + `pytest` + `httpx` cho serverless | Đã cắt còn 6 package thực dùng |
| `requirements.txt` và `pyproject.toml` lệch nhau | Đã đồng bộ |
| Không có route fallback → deep link 404 | Đã thêm SPA fallback |

Kích thước repo: 1,7 MB → 660 KB.

## F. Bảo mật

- `ALLOWED_ORIGINS` rỗng mặc định → CORS chặt. Đúng.
- `/api/google-sheets-test` có `DIAGNOSTIC_TOKEN` gate. Đúng.
- Lỗi trả về client đã được che (`"Không thể lập lá số..."`), stack trace chỉ vào log. Đúng.
- **Cần lưu ý**: mọi file trong repo đều servable tĩnh trên Vercel. `system_prompts/*.txt` và
  `ai_modes/*.txt` sẽ đọc được qua URL trực tiếp. Nếu prompt là tài sản riêng, hãy chuyển chúng
  vào biến môi trường hoặc thêm vào `.vercelignore` **và** đọc từ nguồn khác.

## G. Test — 10 case đỏ, engine đúng, test sai

Đã kiểm chứng thủ công từng case:

1. `test_tam_phuong_tu_chinh_contains_four_houses` kỳ vọng `{1,5,7,11}` cho cung Tý.
   Tam hợp của Tý là **Thân–Tý–Thìn** → cung_so `{9,1,5}`, xung chiếu Ngọ → `7`.
   Đúng phải là `{1,5,7,9}` — chính là kết quả engine trả. **Cung 11 = Tuất không tam hợp với Tý.**
2. `test_tieu_van.py` (5 case): ví dụ `calc("Tý","Ngọ","Nữ")` kỳ vọng dừng ở **Mùi**.
   Từ cung khởi Tuất, đi 6 bước — thuận hay nghịch đều ra **Thìn** (6 là nửa vòng 12).
   Kỳ vọng "Mùi" bất khả thi về mặt số học. Engine trả Thìn.
3. `test_ai_context` kỳ vọng `schema_version == "3.2-..."`, code đã lên `"3.5-..."`.
   Test chưa cập nhật theo changelog.

**Khuyến nghị**: sửa test cho khớp engine, không sửa engine theo test. Chưa tự sửa vì đây là
quy tắc nghiệp vụ Tử Vi — cần bạn xác nhận trước.

## H. Việc nên làm tiếp

1. Sửa 10 test sai (mục G) — cần bạn chốt quy tắc.
2. Gộp 2 lần gọi `build_ai_context()` còn 1 → cắt ~50 % thời gian `deepcopy`.
3. Ba định nghĩa quan hệ cung song song: `engine/geometry.py`, `rules/relationships.py`,
   `tu_vi_calculator.relation()`. Ba bảng Lục Hợp, ba hàm normalize Địa Chi giống nhau.
   Nên gộp về `rules/relationships.py`. Rủi ro drift nếu sửa một chỗ.
4. `tuvi_engine/van_calculator.py` dùng `from .van_calculator_legacy import *` — che mất
   ranh giới API. 17 KB legacy nên được inline hoặc đặt tên rõ.
5. `books_cache.json` được đọc nhưng không tồn tại — hoặc bỏ hẳn, hoặc commit file thật.
