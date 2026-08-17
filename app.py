#!/usr/bin/env python3
import base64
import json
import os
from pathlib import Path
import time

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

# --- 2. CSS CỐ ĐỊNH GIAO DIỆN & TẠO KHUNG CUỘN RIÊNG ---
st.markdown(
    """
    <style>
    /* Nền chung Dark Mode */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }

    /* Tiêu đề ứng dụng */
    .main-header {
        text-align: center;
        color: #f6d365;
        font-size: 2rem;
        font-weight: bold;
        padding: 10px 0;
    }

    /* Khung chứa kết quả luận giải có thanh cuộn riêng */
    .scrollable-result-box {
        background-color: #161922;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 20px;
        height: 65vh; /* Cố định chiều cao theo màn hình */
        overflow-y: auto; /* Tự động tạo thanh cuộn riêng */
        line-height: 1.6;
        color: #e2e8f0;
    }

    /* Tùy chỉnh thanh cuộn đẹp mắt */
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

    /* Khung Chat cuộn riêng */
    .scrollable-chat-box {
        height: 60vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 3. CẤU HÌNH VÀ HÀM XỬ LÝ API ---
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


# --- 4. HIỂN THỊ TIÊU ĐỀ & TABS ---
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

    # Khung trái: Cố định thông số đầu vào
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

    # Khung phải: Nơi hiển thị kết quả cuộn độc lập
    with col2:
        st.subheader("📜 Kết Quả Luận Giải")

        if btn_analyze:
            if not uploaded_file:
                st.warning("⚠️ Vui lòng tải lên ảnh lá số!")
            elif not API_KEY:
                st.error("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY!")
            else:
                progress_bar = st.progress(0, text="0% - Đang khởi tạo...")

                try:
                    time.sleep(0.2)
                    progress_bar.progress(
                        20, text="20% - 📸 Đang đọc & nhận diện hình ảnh..."
                    )
                    image = Image.open(uploaded_file).convert("RGB")

                    time.sleep(0.2)
                    progress_bar.progress(
                        45, text="45% - ☯️ Đối chiếu Tinh Đẩu & Cách Cục..."
                    )
                    system_instruction = load_system_instruction()

                    time.sleep(0.2)
                    progress_bar.progress(
                        70, text="70% - 🔮 Truy vấn Phú & Sách Tử Vi..."
                    )
                    prompt_text = (
                        f"YÊU CẦU LUẬN GIẢI LÁ SỐ TỬ VI:\n"
                        f"- Năm Tiểu Hạn cần xem: {year_input}\n"
                        f"- Yêu cầu bổ sung từ gia chủ: {note_input}\n\n"
                        f"Hãy tiến hành đọc ảnh lá số và luận giải chi tiết, đầy đủ theo đúng bộ quy tắc hệ thống."
                    )

                    progress_bar.progress(
                        90, text="90% - 📝 Gemini AI đang tổng hợp bài luận..."
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

                    progress_bar.progress(
                        100, text="100% - Hoàn tất luận giải!"
                    )
                    time.sleep(0.3)
                    progress_bar.empty()

                    if response and response.text:
                        st.session_state.analysis_result = response.text
                    else:
                        st.session_state.analysis_result = (
                            "Không nhận được phản hồi từ AI."
                        )

                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Lỗi xử lý: {str(e)}")

        # Khung hiển thị có thanh cuộn riêng
        if st.session_state.analysis_result:
            st.markdown(
                f'<div class="scrollable-result-box">{st.session_state.analysis_result}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Chưa có kết quả luận giải. Vui lòng tải lá số lên để phân tích."
            )

# --- TAB 2: TRÒ CHUYỆN AI ---
with tab2:
    st.subheader("💬 Trò Chuyện Cùng AI")

    # Container trò chuyện riêng
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
    st.subheader("📚 Dữ Liệu Phú & Sách Trong Cache")
    titles, total_size = load_cached_books_safe()

    st.metric(label="Dung lượng Cache", value=total_size)
    st.write("---")

    if titles:
        for t in titles:
            st.markdown(f"- {t}")
    else:
        st.info("Chưa có dữ liệu sách hoặc tệp JSON đang trống.")
