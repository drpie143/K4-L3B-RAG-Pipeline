"""Chatbot RAG — Pháp luật cho hộ kinh doanh.

Chạy: streamlit run app.py

Giao diện gồm 3 trang (Chatbot, Đánh giá, Kho tài liệu) trong thư mục ui/.
Mọi lời gọi backend đi qua ui/backend.py; xem docstring file đó để biết
cách nối pipeline RAG thật vào giao diện.
"""

import streamlit as st
from dotenv import load_dotenv

from ui import backend
from ui.page_chat import chat_page
from ui.page_corpus import corpus_page
from ui.page_evaluation import evaluation_page
from ui.theme import inject_css


load_dotenv()

st.set_page_config(
    page_title="Trợ lý Pháp luật Hộ kinh doanh",
    page_icon="⚖️",
    layout="wide",
)
inject_css()

navigation = st.navigation(
    [
        st.Page(chat_page, title="Chatbot", icon=":material/forum:", default=True),
        st.Page(evaluation_page, title="Đánh giá", icon=":material/monitoring:", url_path="evaluation"),
        st.Page(corpus_page, title="Kho tài liệu", icon=":material/library_books:", url_path="corpus"),
    ],
    position="top",
)

with st.sidebar:
    st.markdown("### :material/balance: Pháp luật Hộ kinh doanh")
    st.caption("Chatbot RAG · hybrid retrieval (dense + BM25 + RRF) · trả lời có citation")
    status = {
        "real": (":green[:material/check_circle:]", "Đang dùng backend RAG thật"),
        "demo": (":orange[:material/science:]", "Chế độ demo · dữ liệu mẫu"),
        "unknown": (":gray[:material/sync:]", "Tự động · dùng backend khi sẵn sàng"),
    }[backend.backend_mode()]
    st.caption(f"{status[0]} {status[1]}")
    st.divider()

navigation.run()

with st.sidebar:
    st.divider()
    st.caption("Dữ liệu cập nhật đến 09/2026 · Nguồn: Công báo điện tử, Báo Chính phủ, VnExpress")
