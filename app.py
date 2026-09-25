import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="💬",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Chủ đề và corpus sẽ được cấu hình sau khi nhóm thống nhất.")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("RAG Chatbot")
st.caption("Câu trả lời chỉ được tạo từ các nguồn đã index và luôn kèm citation.")


def show_sources(sources: list[dict]) -> None:
    """Hiển thị nguồn retrieval theo cách có thể kiểm chứng."""
    if not sources:
        return
    with st.expander(f"Nguồn đã dùng ({len(sources)})"):
        for index, source in enumerate(sources, 1):
            metadata = source["metadata"]
            st.markdown(f"**[S{index}] {metadata['title']}**")
            if metadata.get("url"):
                st.markdown(f"[{metadata['source']}]({metadata['url']})")
            else:
                st.caption(metadata["source"])
            st.caption(
                f"Method: {source['retrieval_method']} · Score: {source['score']:.4f}"
            )
            st.text(source["content"][:500])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        show_sources(message.get("sources", []))

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm nguồn và tạo câu trả lời..."):
            try:
                result = generate_with_citation(query, top_k=top_k)
            except Exception as error:
                result = {
                    "answer": f"Không thể xử lý yêu cầu lúc này: {error}",
                    "sources": [],
                    "retrieval_source": "none",
                }
        st.markdown(result["answer"])
        show_sources(result["sources"])

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })
