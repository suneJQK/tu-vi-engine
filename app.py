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

# --- 1. CẤU HÌNH STREAMLIT ---
st.set_page_config(
    page_title="Tử Vi Đẩu Số Engine",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Ẩn giao diện mặc định
st.markdown(
    """
    <style>
    header, footer, #MainMenu, [data-testid="stSidebar"] { display: none !important; }
    .block-container { padding: 0rem !important; margin: 0rem !important; max-width: 100% !important; }
    iframe { display: block; width: 100vw !important; border: none; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 2. CẤU HÌNH ĐƯỜNG DẪN & SYSTEM PROMPT ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
BASE_DIR = Path(__file__).parent
SYSTEM_PROMPT_FILE = BASE_DIR / "system_prompts" / "system_instruction.txt"
ENGINE_FILE = BASE_DIR / "tu_vi_engine.json"
CACHE_FILE = BASE_DIR / "books_cache.json"
GEMINI_MODEL = "gemini-2.5-flash"

# Session State
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = (
        "<p style='color: #a0aec0;'>Chưa có kết quả luận giải. Vui lòng tải lá số lên để phân tích.</p>"
    )
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def load_system_instruction():
    """Đọc system prompt từ system_prompts/system_instruction.txt"""
    if SYSTEM_PROMPT_FILE.exists():
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    elif ENGINE_FILE.exists():
        with open(ENGINE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()[:30000]
    return "Bạn là chuyên gia Tử Vi Đẩu Số. Hãy luận giải đầy đủ theo lá số được cung cấp."


def load_cached_books_safe():
    """Đọc dữ liệu kho sách"""
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


def process_gemini_analysis(image, year, note):
    """Gọi Gemini API phân tích lá số"""
    if not API_KEY:
        return "<p style='color: #fc8181;'>❌ Lỗi: Chưa cấu hình GEMINI_API_KEY trong Secrets!</p>"
    try:
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
            contents=[image, prompt_text],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            ),
        )
        return response.text if response and response.text else "Không nhận được phản hồi từ AI."
    except Exception as e:
        return f"<p style='color: #fc8181;'>❌ Lỗi xử lý API: {str(e)}</p>"


def process_gemini_chat(message):
    """Xử lý trò chuyện cùng AI"""
    if not API_KEY:
        return "Chưa cấu hình GEMINI_API_KEY!"
    try:
        client = genai.Client(api_key=API_KEY)
        chat_prompt = f"BÀI LUẬN GỐC:\n{st.session_state.analysis_result}\n\nCÂU HỎI MỚI: {message}"
        response = client.models.generate_content(
            model=GEMINI_MODEL, contents=[chat_prompt]
        )
        return response.text if response and response.text else "AI không có phản hồi."
    except Exception as e:
        return f"Lỗi: {str(e)}"


# --- 3. CUSTOM COMPONENT SETUP ---
# SỬA LỖI TẠI ĐÂY: Tham số 'path' phải trỏ đến thư mục chứa index.html (BASE_DIR)
tu_vi_component = components.declare_component("tu_vi_component", path=str(BASE_DIR))

# Lấy thông tin kho sách
titles, total_size = load_cached_books_safe()

# Trình truyền dữ liệu từ Python xuống JS Component
component_value = tu_vi_component(
    key="tu_vi_engine_ui",
    analysis_result=st.session_state.analysis_result,
    books_titles=titles,
    books_size=total_size,
    chat_history=st.session_state.chat_history,
)

# --- 4. HỨNG VÀ XỬ LÝ DỮ LIỆU TỪ HTML TRUYỀN LÊN ---
if component_value and isinstance(component_value, dict):
    action = component_value.get("action")

    if action == "ANALYZE":
        base64_str = component_value.get("image_base64", "")
        year = component_value.get("year", 2026)
        note = component_value.get("note", "")

        if "," in base64_str:
            base64_data = base64_str.split(",")[1]
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            # Xử lý luận giải với Gemini API
            res = process_gemini_analysis(image, year, note)
            st.session_state.analysis_result = res
            st.rerun()

    elif action == "CHAT":
        user_msg = component_value.get("message", "")
        if user_msg:
            ai_reply = process_gemini_chat(user_msg)
            st.session_state.chat_history.append((user_msg, ai_reply))
            st.rerun()
