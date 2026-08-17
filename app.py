#!/usr/bin/env python3
import base64
import json
import os
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

# --- 1. CẤU HÌNH GIAO DIỆN STREAMLIT ---
st.set_page_config(
    page_title="Tử Vi Đẩu Số Engine",
    page_icon="☯️",
    layout="wide",
)

# Custom CSS giao diện Tối & Khung cuộn độc lập
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .main-header {
        text-align: center;
        color: #f6d365;
        font-size: 2rem;
        font-weight: bold;
        padding: 10px 0;
    }
    .scrollable-result-box {
        background-color: #161922;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 20px;
        height: 65vh;
        overflow-y: auto;
        line-height: 1.6;
        color: #e2e8f0;
    }
    .scrollable-result-box::-webkit-scrollbar {
        width: 8px;
    }
    .scrollable-result-box::-webkit-scrollbar-track {
        background: #1a202c;
        border-radius: 10px;
    }
    .scrollable-result-box::-webkit-scrollbar-thumb {
        background: #4a5568;
        border-radius: 10px;
    }
    .scrollable-result-box::-webkit-scrollbar-thumb:hover {
        background: #f6d365;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 2. CẤU HÌNH ĐƯỜNG DẪN VÀ THÔNG SỐ ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
BASE_DIR = Path(__file__).parent
SYSTEM_PROMPT_FILE = BASE_DIR / "system_prompts" / "system_instruction.txt"
ENGINE_FILE = BASE_DIR / "tu_vi_engine.json"
CACHE_FILE = BASE_DIR / "books_cache.json"
GEMINI_MODEL = "gemini-2.5-flash"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- 3. CÁC HÀM XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_system_instruction():
    if SYSTEM_PROMPT_FILE.exists():
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    elif ENGINE_FILE.exists():
        with open(ENGINE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()[:30000]
    return "Bạn là chuyên gia Tử Vi Đẩu Số. Hãy luận giải đầy đủ theo lá số được cung cấp."


def load_cached_books_safe():
    if not CACHE_FILE.exists():
        return [], "0 KB"

    try:
        file_size_bytes = CACHE_FILE.stat().st_size
        size_str = (
            f"{file_size_bytes / 1024:.1f} KB"
            if file_size_bytes >= 1024
            else f"{file_size_bytes} Bytes"
        )

        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        titles = []
        if isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    title_val = (
                        item.get("title")
                        or item.get("name")
                        or list(item.values())[0]
                    )
                    titles.append(f"{idx+1}. {str(title_val)[:60]}")
                elif isinstance(item, str):
                    clean_str = item.strip().replace("\n", " ")
                    titles.append(f"{idx+1}. {clean_str[:60]}...")
        elif isinstance(data, dict):
            for idx, (k, v) in enumerate(data.items()):
                titles.append(f"{idx+1}. {k}")

        return titles, size_str

    except Exception as e:
        if CACHE_FILE.exists():
            file_size_bytes = CACHE_FILE.stat().st_size
            return [
                f"⚠️ File JSON lỗi cú pháp: {str(e)}"
            ], f"{file_size_bytes / 1024:.1f} KB"
        return [], "0 KB"


# --- 4. GIAO DIỆN CHÍNH ---
st.markdown(
    '<div class="main-header">☯️ TỬ VI ĐẨU SỐ ENGINE</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(
    ["⚙️ Luận Giải Lá Số", "💬 Trò Chuyện AI", "📚 Kho Dữ Liệu Sách"]
)

# --- TAB 1: LUẬN GIẢI LÁ SỐ ---
with tab1:
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.subheader("📸 Cấu Hình Luận Giải")
        uploaded_file = st.file_uploader(
            "Tải ảnh lá số Tử Vi", type=["png", "jpg", "jpeg"]
        )
        year_input = st.number_input(
            "📅 Năm Tiểu Hạn",
            min_value=1950,
            max_value=2050,
            value=2026,
        )
        note_input = st.text_area(
            "📝 Ghi chú thêm", value="Phân tích kỹ Cách Cục và Vận Hạn."
        )

        btn_analyze = st.button(
            "🔮 BẮT ĐẦU LUẬN GIẢI", use_container_width=True, type="primary"
        )

    with col2:
        st.subheader("📜 Kết Quả Luận Giải")
        result_placeholder = st.empty()

        if btn_analyze:
            if not uploaded_file:
                st.warning("⚠️ Vui lòng tải lên ảnh lá số!")
            elif not API_KEY:
                st.error("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY!")
            else:
                with st.status(
                    "🔮 AI đang đọc lá số & phân tích...", expanded=True
                ) as status:
                    try:
                        image = Image.open(uploaded_file).convert("RGB")
                        system_instruction = load_system_instruction()

                        prompt_text = (
                            f"YÊU CẦU LUẬN GIẢI LÁ SỐ TỬ VI:\n"
                            f"- Năm Tiểu Hạn cần xem: {year_input}\n"
                            f"- Yêu cầu bổ sung: {note_input}\n\n"
                            f"Hãy tiến hành đọc ảnh lá số và luận giải chi tiết, đầy đủ."
                        )

                        client = genai.Client(api_key=API_KEY)

                        response_stream = client.models.generate_content_stream(
                            model=GEMINI_MODEL,
                            contents=[image, prompt_text],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.3,
                            ),
                        )

                        full_text = ""
                        for chunk in response_stream:
                            if chunk.text:
                                full_text += chunk.text
                                result_placeholder.markdown(
                                    f'<div class="scrollable-result-box">{full_text}</div>',
                                    unsafe_allow_html=True,
                                )

                        st.session_state.analysis_result = full_text
                        status.update(
                            label="✅ Luận giải hoàn tất!",
                            state="complete",
                            expanded=False,
                        )

                    except Exception as e:
                        status.update(
                            label="❌ Lỗi xử lý!", state="error", expanded=True
                        )
                        st.error(f"Chi tiết lỗi: {str(e)}")

        if st.session_state.analysis_result and not btn_analyze:
            result_placeholder.markdown(
                f'<div class="scrollable-result-box">{st.session_state.analysis_result}</div>',
                unsafe_allow_html=True,
            )
        elif not st.session_state.analysis_result:
            result_placeholder.info(
                "Chưa có kết quả luận giải. Vui lòng tải lá số lên để phân tích."
            )

# --- TAB 2: TRÒ CHUYỆN AI ---
with tab2:
    st.subheader("💬 Trò Chuyện Cùng AI")

    chat_container = st.container(height=450)
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if user_prompt := st.chat_input("Nhập câu hỏi về lá số..."):
        st.session_state.chat_history.append(
            {"role": "user", "content": user_prompt}
        )
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                if not API_KEY:
                    st.error("Chưa cấu hình GEMINI_API_KEY!")
                else:
                    with st.spinner("AI đang suy nghĩ..."):
                        try:
                            client = genai.Client(api_key=API_KEY)
                            chat_prompt = (
                                f"BÀI LUẬN GỐC:\n{st.session_state.analysis_result or 'Chưa có'}\n\n"
                                f"CÂU HỎI MỚI: {user_prompt}"
                            )
                            response = client.models.generate_content(
                                model=GEMINI_MODEL, contents=[chat_prompt]
                            )
                            bot_reply = (
                                response.text
                                if response and response.text
                                else "Không nhận được phản hồi."
                            )
                            st.markdown(bot_reply)
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": bot_reply}
                            )
                        except Exception as e:
                            st.error(f"Lỗi: {str(e)}")

# --- TAB 3: KHO DỮ LIỆU SÁCH ---
with tab3:
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.subheader("📚 Dữ Liệu Phú & Sách Trong Cache")
    with col_btn:
        if st.button("🔄 Cập nhật Cache"):
            st.rerun()

    titles, total_size = load_cached_books_safe()

    st.metric(label="Dung lượng Cache", value=total_size)
    st.write("---")

    if titles:
        for t in titles:
            st.markdown(f"- {t}")
    else:
        st.info("Chưa có dữ liệu sách hoặc tệp JSON đang trống.")
