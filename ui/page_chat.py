"""Trang Chatbot: hỏi đáp có citation."""

import json
import uuid

import streamlit as st

from . import backend, mock_data
from .components import render_answer
from .theme import hero, icon


RETRIEVAL_OPTIONS = {"Hybrid + RRF": True, "Dense-only": False}
USER_AVATAR = ":material/person:"
BOT_AVATAR = ":material/balance:"


def _settings() -> tuple[int, bool, bool]:
    with st.sidebar:
        st.subheader(":material/tune: Cấu hình truy xuất")
        top_k = st.slider("Số đoạn nguồn (top-k)", 3, 10, 5, help="Số chunk đưa vào context cho LLM.")
        toggle_ok = backend.supports_retrieval_toggle()
        mode = st.segmented_control(
            "Chiến lược retrieval",
            list(RETRIEVAL_OPTIONS),
            default="Hybrid + RRF",
            disabled=not toggle_ok,
            help=(
                "So sánh A/B: Dense-only (Config A) và Hybrid + RRF (Config B)."
                if toggle_ok else
                "Backend chưa nhận tham số use_reranking nên luôn chạy cấu hình mặc định."
            ),
        ) or "Hybrid + RRF"
        debug = st.toggle("Hiện chẩn đoán", help="Kiểm tra schema và xem JSON trả về từ backend.")
        st.divider()
        if st.button("Xóa hội thoại", icon=":material/delete_sweep:", width="stretch", disabled=not st.session_state.messages):
            st.session_state.messages = []
            st.rerun()
    return top_k, RETRIEVAL_OPTIONS[mode], debug


def _ask_example(question: str) -> None:
    st.session_state.pending_query = question


def _empty_state() -> None:
    st.html(
        f'<div class="empty-state"><div class="big">{icon("forum")}</div>'
        "<p><b>Hỏi bất cứ điều gì về pháp luật cho hộ kinh doanh</b><br>"
        '<span style="opacity:0.75">Đăng ký hộ kinh doanh · Thuế GTGT, TNCN · Hóa đơn điện tử · '
        "Kinh doanh trên sàn thương mại điện tử</span></p></div>"
    )
    st.caption("Thử một câu hỏi mẫu:")
    columns = st.columns(2)
    for index, question in enumerate(mock_data.EXAMPLE_QUESTIONS):
        out_of_domain = index == len(mock_data.EXAMPLE_QUESTIONS) - 1
        columns[index % 2].button(
            question, key=f"example_{index}", on_click=_ask_example, args=(question,),
            icon=":material/block:" if out_of_domain else ":material/help:", width="stretch",
            help="Câu hỏi ngoài phạm vi, để thử safe refusal" if out_of_domain else None,
        )


def _debug_panel(message: dict) -> None:
    with st.expander("Chẩn đoán", icon=":material/bug_report:", expanded=False):
        problem = backend.contract_problem(message["raw"]) if message.get("raw") else None
        if problem:
            st.warning(f"Kết quả chưa đúng contract `GenerationResult`: {problem}")
        elif message.get("raw"):
            st.success("Kết quả đúng contract `GenerationResult`.")
        st.code(json.dumps(message.get("raw", {}), ensure_ascii=False, indent=2), language="json")


def _render_history(debug: bool) -> None:
    last = len(st.session_state.messages) - 1
    for index, message in enumerate(st.session_state.messages):
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            if message["role"] == "user":
                st.markdown(message["content"])
                continue
            render_answer(message, expanded=index == last)
            st.feedback("thumbs", key=f"feedback_{message['id']}")
            if debug:
                _debug_panel(message)


def _answer(query: str, top_k: int, use_reranking: bool) -> dict:
    message = {"role": "assistant", "id": uuid.uuid4().hex, "query": query, "top_k": top_k}
    with st.spinner("Đang tìm nguồn liên quan và soạn câu trả lời…"):
        try:
            result = backend.ask(query, top_k=top_k, use_reranking=use_reranking)
        except Exception as error:  # backend lỗi không được làm UI crash
            return {**message, "content": f"Không thể xử lý yêu cầu lúc này: {error}", "error": True,
                    "sources": [], "retrieval_source": "none"}
    raw = {key: result.get(key) for key in ("answer", "sources", "retrieval_source")}
    return {
        **message,
        "content": result.get("answer") or mock_data.SAFE_REFUSAL,
        "sources": result.get("sources") or [],
        "retrieval_source": result.get("retrieval_source", "none"),
        "latency_ms": result.get("latency_ms"),
        "mode": result.get("mode"),
        "raw": raw,
    }


def chat_page() -> None:
    st.session_state.setdefault("messages", [])
    top_k, use_reranking, debug = _settings()

    hero(
        "balance",
        "Trợ lý Pháp luật Hộ kinh doanh",
        "Trả lời dựa trên nghị định và bài viết chính thức · mỗi ý đều kèm nguồn [S1], [S2] để kiểm chứng",
    )

    # chat_input luôn ghim ở cuối trang nên có thể đọc trước khi vẽ lịch sử.
    query = st.chat_input("Nhập câu hỏi về đăng ký, thuế, hóa đơn của hộ kinh doanh…")
    query = query or st.session_state.pop("pending_query", None)

    if not st.session_state.messages and not query:
        _empty_state()
    _render_history(debug)

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(query)
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            answer = _answer(query, top_k, use_reranking)
        st.session_state.messages.append(answer)
        st.rerun()
