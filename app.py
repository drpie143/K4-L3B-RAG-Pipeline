import html
import re

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

EXAMPLES = [
    "Một cá nhân được đăng ký bao nhiêu hộ kinh doanh trên toàn quốc?",
    "Tên hộ kinh doanh phải gồm những thành tố nào?",
    "Hộ kinh doanh có doanh thu năm trên 01 tỷ đồng có bắt buộc dùng hóa đơn điện tử không?",
]
METHOD_LABELS = {
    "dense": "Dense",
    "bm25": "BM25",
    "hybrid": "Hybrid",
    "pageindex": "PageIndex",
    "none": "Không truy xuất",
}
DOC_TYPE_LABELS = {
    "legal": "Văn bản pháp luật",
    "news": "Bài hướng dẫn",
}

st.set_page_config(
    page_title="Trợ lý pháp luật hộ kinh doanh",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="auto",
)
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; max-width: 860px; }
    .welcome {
        background: #fffdf8;
        border: 1px solid #e4ddd0;
        border-radius: 16px;
        padding: 1.1rem 1.2rem 0.4rem;
        margin-bottom: 0.8rem;
    }
    .welcome h2 { margin: 0 0 0.35rem; font-size: 1.35rem; }
    .welcome p { color: #5c564c; margin: 0 0 0.8rem; }
    .answer { line-height: 1.65; }
    a.cite, span.cite {
        display: inline-block;
        background: #1f4d45;
        color: #fff !important;
        border-radius: 999px;
        padding: 0 0.45rem;
        font-size: 0.78rem;
        font-weight: 650;
        text-decoration: none;
        margin: 0 0.12rem;
        line-height: 1.45rem;
    }
    .source-card {
        background: #fffdf8;
        border: 1px solid #e4ddd0;
        border-left: 4px solid #1f4d45;
        border-radius: 12px;
        padding: 0.75rem 0.9rem 0.35rem;
        margin: 0.45rem 0 0.15rem;
    }
    .source-title { margin: 0.15rem 0; }
    .meta { color: #5c564c; font-size: 0.86rem; }
    .pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.05rem 0.5rem;
        margin-right: 0.3rem;
        background: #e7f0ee;
        color: #1f4d45;
        font-size: 0.78rem;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_generation" not in st.session_state:
    st.session_state.pending_generation = None


def render_answer(answer: str, source_count: int) -> None:
    """Đánh dấu [S#] thành thẻ citation trỏ tới nguồn tương ứng."""

    def cite(match: re.Match) -> str:
        number = int(match.group(1))
        label = html.escape(match.group(0))
        if 1 <= number <= source_count:
            return f'<a class="cite" href="#source-{number}">S{number}</a>'
        return label

    body = re.sub(r"\[S(\d+)\]", cite, html.escape(answer)).replace("\n", "<br>")
    st.markdown(f'<div class="answer">{body}</div>', unsafe_allow_html=True)


def show_sources(sources: list[dict]) -> None:
    """Hiển thị nguồn, phương thức truy xuất và điểm số."""
    if not sources:
        st.caption("Không có đoạn nguồn được trích dẫn.")
        return
    for index, source in enumerate(sources, 1):
        metadata = source.get("metadata") or {}
        title = html.escape(str(metadata.get("title") or "Không có tiêu đề"))
        method = METHOD_LABELS.get(source.get("retrieval_method"), source.get("retrieval_method", ""))
        doc_type = DOC_TYPE_LABELS.get(metadata.get("doc_type"), metadata.get("doc_type") or "")
        score = source.get("score")
        score_text = f"{float(score):.3f}" if isinstance(score, (int, float)) else "—"
        details = []
        for key, label in (
            ("number", "Số hiệu"),
            ("issued", "Ban hành"),
            ("effective", "Hiệu lực"),
            ("date_published", "Đăng"),
            ("section", "Mục"),
        ):
            if metadata.get(key):
                details.append(f"{label}: {html.escape(str(metadata[key]))}")
        detail_html = f'<div class="meta">{" · ".join(details)}</div>' if details else ""
        st.markdown(
            f"""
            <div class="source-card" id="source-{index}">
                <span class="cite">S{index}</span>
                <span class="pill">{html.escape(str(method))}</span>
                <span class="pill">{html.escape(str(doc_type))}</span>
                <span class="pill">Điểm {html.escape(score_text)}</span>
                <div class="source-title"><strong>{title}</strong></div>
                {detail_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        url = metadata.get("url")
        source_name = metadata.get("source") or ""
        if url:
            st.markdown(f"[{source_name}]({url})")
        elif source_name:
            st.caption(source_name)
        with st.expander("Đoạn đã dùng", expanded=False):
            st.text(source.get("content") or "")


def answer_question(query: str, top_k: int) -> dict:
    try:
        result = generate_with_citation(query, top_k=top_k)
    except Exception as error:
        result = {
            "answer": "Không thể xử lý yêu cầu lúc này.",
            "sources": [],
            "retrieval_source": "none",
            "error": str(error),
        }
    result.setdefault("error", "")
    return result


with st.sidebar:
    st.header("Pháp luật hộ kinh doanh")
    st.caption("Trả lời từ văn bản pháp luật và bài hướng dẫn đã thu thập. Mỗi ý chính kèm citation.")
    top_k = st.slider("Số đoạn nguồn", 3, 10, 5)
    st.divider()
    st.markdown(
        "**Cách truy xuất**\n\n"
        "Dense và BM25 được gộp bằng RRF. Khi điểm dense thấp, pipeline chuyển sang PageIndex."
    )
    if st.button("Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.session_state.pending_generation = None
        st.rerun()

st.title("Trợ lý pháp luật cho hộ kinh doanh")
st.caption("Câu trả lời bám nguồn đã index. Citation [S#] dẫn tới đoạn văn được dùng.")

query = st.session_state.pop("pending_query", None)
typed = st.chat_input("Nhập câu hỏi về hộ kinh doanh...")
if typed:
    query = typed

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.pending_generation = int(top_k)
    st.rerun()

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome">
            <h2>Hỏi một tình huống của hộ kinh doanh</h2>
            <p>Chọn câu gợi ý hoặc tự nhập câu hỏi. Câu ngoài nguồn sẽ được từ chối, không bịa quy định.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for index, example in enumerate(EXAMPLES):
        if st.button(example, key=f"example-{index}", use_container_width=True):
            st.session_state.pending_query = example
            st.rerun()


def show_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message["role"] != "assistant":
            st.markdown(message["content"])
            return
        sources = message.get("sources") or []
        render_answer(message["content"], len(sources))
        method = METHOD_LABELS.get(
            message.get("retrieval_source"),
            message.get("retrieval_source") or "Không truy xuất",
        )
        st.caption(f"Nguồn truy xuất: {method}")
        if message.get("error"):
            st.warning(message["error"])
        show_sources(sources)


for message in st.session_state.messages:
    show_message(message)

if st.session_state.get("pending_generation"):
    question = next(
        message["content"]
        for message in reversed(st.session_state.messages)
        if message["role"] == "user"
    )
    with st.spinner("Đang tìm nguồn và soạn câu trả lời..."):
        result = answer_question(question, int(st.session_state.pending_generation))
    st.session_state.pending_generation = None
    assistant = {
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "retrieval_source": result.get("retrieval_source", "none"),
        "error": result.get("error", ""),
    }
    st.session_state.messages.append(assistant)
    show_message(assistant)
