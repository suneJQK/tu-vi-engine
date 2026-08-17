#!/usr/bin/env python3
import base64
import json
import os
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="Tử Vi Đẩu Số Engine",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Secrets & Configs
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
BASE_DIR = Path(__file__).parent
ENGINE_FILE = BASE_DIR / "tu_vi_engine.json"
CACHE_FILE = BASE_DIR / "books_cache.json"
INDEX_FILE = BASE_DIR / "index.html"
GEMINI_MODEL = "gemini-2.5-flash"

# Session State
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Xử lý gọi Gemini API
def process_gemini(uploaded_file, year, note):
    if not API_KEY:
        return "❌ Lỗi: Chưa cấu hình GEMINI_API_KEY trong Secrets!"
    try:
        image = Image.open(uploaded_file).convert("RGB")
        engine_rules = ""
        if ENGINE_FILE.exists():
            with open(ENGINE_FILE, "r", encoding="utf-8") as f:
                engine_rules = f.read()[:30000]

        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                image,
                f"Năm luận giải: {year}. Yêu cầu bổ sung: {note}",
            ],
            config=types.GenerateContentConfig(
                system_instruction=f"BỘ QUY TẮC NGUYÊN TẮC LUẬN GIẢI:\n{engine_rules}",
            ),
        )
        return (
            response.text
            if response and response.text
            else "Không nhận được phản hồi từ AI."
        )
    except Exception as e:
        return f"❌ Lỗi xử lý API: {str(e)}"


# Đọc cache sách an toàn (Chống lỗi JSONDecodeError)
def load_books_safe():
    if not CACHE_FILE.exists():
        return [], "0 KB"
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return [], "0 KB"
            data = json.loads(content)
            titles = [
                item.get("title", f"Mục {i+1}")
                for i, item in enumerate(data)
                if isinstance(item, dict)
            ]
            return titles, f"{len(content)/1024:.1f} KB"
    except Exception:
        return [], "0 KB"


# CSS Custom
st.markdown(
    """
    <style>
    header, footer, #MainMenu { visibility: hidden; }
    .stApp { background-color: #0e1117; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("☯️ Tử Vi Đẩu Số Engine")

# Giao diện Tabs native Streamlit
tab1, tab2, tab3 = st.tabs([
    "⚙️ Luận Giải Lá Số",
    "💬 Trò Chuyện AI",
    "📚 Kho Dữ Liệu Sách",
])

with tab1:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("⚙️ Cấu Hình Luận Giải")
        uploaded_file = st.file_uploader(
            "📸 Tải ảnh lá số Tử Vi", type=["jpg", "png", "jpeg", "webp"]
        )
        selected_year = st.number_input("📅 Năm Tiểu Hạn", 1950, 2050, 2026)
        user_note = st.text_area(
            "📝 Ghi chú thêm", "Phân tích kỹ Cách Cục và Vận Hạn."
        )
        btn_submit = st.button("🔮 BẮT ĐẦU LUẬN GIẢI", type="primary")

    with col2:
        st.subheader("📜 Kết Quả Luận Giải")
        if btn_submit:
            if uploaded_file is not None:
                with st.spinner("⚡ AI đang phân tích lá số..."):
                    res = process_gemini(uploaded_file, selected_year, user_note)
                    st.session_state.analysis_result = res
            else:
                st.warning("Vui lòng tải lên file ảnh lá số trước!")

        if st.session_state.analysis_result:
            st.markdown(st.session_state.analysis_result)
        else:
            st.info("Chưa có kết quả luận giải. Nhấn nút phía bên trái để bắt đầu.")

with tab2:
    st.subheader("💬 Trò Chuyện Cùng AI")
    for user_msg, ai_msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(user_msg)
        with st.chat_message("assistant"):
            st.write(ai_msg)

    chat_input = st.chat_input("Nhập câu hỏi về lá số...")
    if chat_input:
        if st.session_state.analysis_result:
            try:
                client = genai.Client(api_key=API_KEY)
                chat_prompt = f"BÀI LUẬN GỐC:\n{st.session_state.analysis_result}\n\nCÂU HỎI MỚI: {chat_input}"
                res = client.models.generate_content(
                    model=GEMINI_MODEL, contents=[chat_prompt]
                )
                st.session_state.chat_history.append((chat_input, res.text))
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")
        else:
            st.warning("Bạn cần thực hiện luận giải lá số ở Tab 1 trước!")

with tab3:
    st.subheader("📚 Dữ Liệu Phú & Sách Trong Cache")
    titles, total_size = load_books_safe()
    st.metric("Dung lượng Cache", total_size)

    if titles:
        for t in titles:
            st.markdown(f"- **{t}**")
    else:
        st.info("Chưa có dữ liệu sách hoặc tệp JSON đang trống.")
