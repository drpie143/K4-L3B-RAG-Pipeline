"""Trang Kho tài liệu: xem các văn bản và bài viết đã chuẩn hóa."""

import re

import pandas as pd
import streamlit as st

from . import backend
from .components import DOC_TYPE_LABELS, chip
from .theme import hero, icon


PREVIEW_CHARS = 40_000


@st.cache_data(show_spinner=False)
def _corpus() -> list[dict]:
    return backend.load_corpus()


def _outline(body: str) -> list[str]:
    return [line.lstrip("# ").strip() for line in body.splitlines() if re.match(r"#{2,3} (Chương|Mục|Điều|Phụ lục)", line)]


def corpus_page() -> None:
    hero("library_books", "Kho tài liệu", "Nguồn dữ liệu chatbot dùng để trả lời · Công báo điện tử và báo chính thống")

    documents = _corpus()
    if not documents:
        st.warning("Chưa có dữ liệu chuẩn hóa. Chạy `python -m src.task3_convert_markdown` trước.", icon=":material/folder_off:")
        return

    legal = [d for d in documents if d["doc_type"] == "legal"]
    news = [d for d in documents if d["doc_type"] == "news"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(":material/gavel: Văn bản pháp luật", len(legal), border=True)
    c2.metric(":material/newspaper: Bài viết", len(news), border=True)
    c3.metric(":material/format_list_numbered: Số Điều luật", sum(d["articles"] for d in legal), border=True)
    c4.metric(":material/text_fields: Tổng ký tự", f"{sum(d['chars'] for d in documents) / 1000:.0f}K", border=True)

    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        kind = st.segmented_control("Loại", ["Tất cả", "Pháp luật", "Bài viết"], default="Tất cả",
                                    key="corpus_kind") or "Tất cả"
    with search_col:
        keyword = st.text_input("Tìm theo tiêu đề", placeholder="VD: hóa đơn, 141/2026, thương mại điện tử…")

    shown = {"Tất cả": documents, "Pháp luật": legal, "Bài viết": news}[kind]
    if keyword:
        shown = [d for d in shown if keyword.lower() in (d["title"] + " " + (d["number"] or "")).lower()]

    table = pd.DataFrame([{
        "Loại": {"legal": "Pháp luật", "news": "Bài viết"}.get(d["doc_type"], d["doc_type"]),
        "Tiêu đề": d["title"],
        "Số hiệu": d["number"] or "",
        "Ban hành / đăng": d["issued"] or d["published"] or "",
        "Hiệu lực": d["effective"] or "",
        "Số Điều": str(d["articles"]) if d["articles"] else "",
        "Ký tự": d["chars"],
        "Nguồn": d["url"],
    } for d in shown])
    st.dataframe(
        table, hide_index=True, width="stretch", height=38 + 35 * len(table),
        column_config={
            "Loại": st.column_config.TextColumn(width="small"),
            "Tiêu đề": st.column_config.TextColumn(width="large"),
            "Số hiệu": st.column_config.TextColumn(width="small"),
            "Ban hành / đăng": st.column_config.TextColumn(width="small"),
            "Hiệu lực": st.column_config.TextColumn(width="small"),
            "Số Điều": st.column_config.TextColumn(width="small"),
            "Ký tự": st.column_config.NumberColumn(format="%d", width="small"),
            "Nguồn": st.column_config.LinkColumn(display_text="Mở ↗", width="small"),
        },
    )
    st.caption(f"{len(shown)}/{len(documents)} tài liệu")

    if not shown:
        return
    st.markdown("#### Xem nội dung")
    index = st.selectbox("Chọn tài liệu", range(len(shown)), format_func=lambda i: shown[i]["title"],
                         label_visibility="collapsed")
    selected = shown[index]
    icon_name, label = DOC_TYPE_LABELS.get(selected["doc_type"], ("description", selected["doc_type"]))
    chips = [chip(f"{icon(icon_name)} {label}", selected["doc_type"]), chip(selected["source"], "muted")]
    if selected["effective"]:
        chips.append(chip(f"Hiệu lực {selected['effective']}", "muted"))
    st.html(f'<div class="src-meta">{"".join(chips)}</div>')

    outline = _outline(selected["body"])
    if outline:
        left, right = st.columns([1, 2.2])
        with left:
            with st.container(height=520, border=True):
                st.markdown("**Mục lục**")
                for item in outline:
                    indent = "" if item.startswith(("Chương", "Mục", "Phụ lục")) else "&nbsp;&nbsp;&nbsp;"
                    weight = "**" if not indent else ""
                    st.markdown(f"{indent}{weight}{item[:90]}{weight}", unsafe_allow_html=True)
        target = right
    else:
        target = st.container()
    with target:
        with st.container(height=520, border=True):
            # Bỏ dòng tiêu đề H1 (đã hiển thị ở ô chọn) để phần xem trước gọn hơn.
            body = re.sub(r"\A\s*# .*\n", "", selected["body"])
            if len(body) > PREVIEW_CHARS:
                st.caption(f"Hiển thị {PREVIEW_CHARS // 1000}K/{len(body) // 1000}K ký tự đầu. "
                           "Xem đầy đủ tại file trong data/standardized.")
                body = body[:PREVIEW_CHARS]
            st.markdown(body)
