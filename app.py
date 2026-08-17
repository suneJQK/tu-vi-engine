#!/usr/bin/env python3
import base64
import io
import json
import os
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH TRANG STREAMLIT (BACKEND MODE) ---
st.set_page_config(
    page_title="Tử Vi Đẩu Số Engine",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Ẩn hoàn toàn giao diện mặc định của Streamlit
st.markdown(
    """
    <style>
    header, footer, #MainMenu, [data-testid="stSidebar"] { display: none !important; }
    .block-container { padding: 0rem !important; margin: 0rem !important; max-width: 100% !important; }
    iframe { display: block; width: 100vw !important; height: 100vh !important; border: none; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 2. CẤU HÌNH HỆ THỐNG & ĐƯỜNG DẪN ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
BASE_DIR = Path(__file__).parent

# Đường dẫn đến tệp system instruction theo đúng cấu trúc trong ảnh: system_prompts/system_instruction.txt
SYSTEM_PROMPT_FILE = BASE_DIR / "system_prompts" / "system_instruction.txt"
ENGINE_FILE = BASE_DIR / "tu_vi_engine.json"
CACHE_FILE = BASE_DIR / "books_cache.json"
INDEX_FILE = BASE_DIR / "index.html"
GEMINI_MODEL = "gemini-2.5-flash"

# Session State quản lý dữ liệu ứng dụng
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = (
        "<p style='color: #a0aec0;'>Chưa có kết quả luận giải. Vui lòng tải lá số lên để phân tích.</p>"
    )
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- 3. ĐỌC SYSTEM PROMPT / NGUYÊN TẮC LUẬN GIẢI ---
def load_system_instruction():
    """Đọc system prompt từ system_prompts/system_instruction.txt"""
    if SYSTEM_PROMPT_FILE.exists():
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    elif ENGINE_FILE.exists():
        with open(ENGINE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()[:30000]
    else:
        return (
            "Bạn là bậc thầy Tử Vi Đẩu Số. Hãy luận giải chi tiết, đầy đủ "
            "về Bản Mệnh, Cách Cục, 12 Cung và Vận Hạn dựa trên ảnh lá số được cung cấp."
        )


# --- 4. BACKEND LOGIC & DỊCH VỤ DỮ LIỆU ---

def load_cached_books_safe():
    """Đọc dữ liệu kho sách từ tệp cache JSON"""
    if not CACHE_FILE.exists():
        return [], "0 KB"
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return [], "0 KB"
            data = json.loads(content)
            titles = []
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if isinstance(item, dict) and "title" in item:
                        titles.append(f"{idx+1}. {item['title']}")
                    elif isinstance(item, str):
                        titles.append(f"{idx+1}. {item[:50]}...")
            return titles, f"{len(content)/1024:.1f} KB"
    except Exception:
        return [], "0 KB"


def process_gemini_analysis(uploaded_file, year, note):
    """Xử lý gọi Gemini API luận giải lá số đầy đủ theo system instruction"""
    if not API_KEY:
        return "<p style='color: #fc8181;'>❌ Lỗi: Chưa cấu hình GEMINI_API_KEY trong Secrets!</p>"
    try:
        image = Image.open(uploaded_file).convert("RGB")
        system_instruction = load_system_instruction()

        prompt_text = (
            f"YÊU CẦU LUẬN GIẢI LÁ SỐ TỬ VI:\n"
            f"- Năm Tiểu Hạn cần xem: {year}\n"
            f"- Yêu cầu bổ sung từ gia chủ: {note}\n\n"
            f"Hãy tiến hành đọc ảnh lá số và luận giải chi tiết, đầy đủ theo đúng bộ quy tắc hệ thống."
        )

        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                image,
                prompt_text,
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            ),
        )
        return response.text if response and response.text else "Không nhận được phản hồi từ AI."
    except Exception as e:
        return f"<p style='color: #fc8181;'>❌ Lỗi xử lý API: {str(e)}</p>"


# --- 5. RENDER VÀ TRUYỀN DỮ LIỆU VÀO INDEX.HTML ---

if INDEX_FILE.exists():
    titles, total_size = load_cached_books_safe()

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    safe_analysis = str(st.session_state.analysis_result)
    safe_chat_history = json.dumps(st.session_state.chat_history, ensure_ascii=False)

    final_html = (
        html_content.replace(
            "/* BOOK_TITLES_DATA */", json.dumps(titles, ensure_ascii=False)
        )
        .replace(
            "/* BOOK_SIZE_DATA */", json.dumps(total_size, ensure_ascii=False)
        )
        .replace(
            "/* CHAT_HISTORY_DATA */", safe_chat_history
        )
        .replace("<!-- ANALYSIS_RESULT -->", safe_analysis)
    )

    components.html(final_html, height=1000, scrolling=True)

else:
    st.error("❌ Không tìm thấy file index.html trong cùng thư mục!")
