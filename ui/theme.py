"""Màu sắc và CSS dùng chung cho giao diện Streamlit.

CSS chỉ dùng màu nền bán trong suốt và `color: inherit` để hiển thị đúng
ở cả chế độ sáng lẫn tối của Streamlit.
"""

import streamlit as st


# Màu chuỗi cho biểu đồ A/B (đã kiểm tra khả năng phân biệt màu cho người mù màu).
SERIES_COLORS = {
    "light": ["#2a78d6", "#eb6834"],
    "dark": ["#3987e5", "#d95926"],
}

CSS = """
<style>
/* ---------- Khung chung ---------- */
.block-container { padding-top: 4.2rem; max-width: 1180px; }
.hero {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 22px; margin-bottom: 18px; border-radius: 14px;
  background: linear-gradient(120deg, rgba(42,120,214,0.14), rgba(27,175,122,0.10));
  border: 1px solid rgba(42,120,214,0.22);
}
.hero-icon { font-size: 2.3rem; line-height: 1; color: #2a78d6; }
.hero h1 { font-size: 1.45rem; margin: 0; padding: 0; }
.hero p { margin: 2px 0 0; opacity: 0.78; font-size: 0.92rem; }

/* ---------- Icon (font Material Symbols mà Streamlit đã tải sẵn) ---------- */
.msi {
  font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal;
  font-size: 1.15em; line-height: 1; vertical-align: -0.2em; display: inline-block;
  font-feature-settings: 'liga'; -webkit-font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased;
}

/* ---------- Chip / badge ---------- */
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 1px 9px; border-radius: 999px; font-size: 0.74rem; font-weight: 600;
  border: 1px solid transparent; white-space: nowrap; line-height: 1.6;
}
.chip-legal   { background: rgba(74,58,167,0.14);  border-color: rgba(74,58,167,0.35); }
.chip-news    { background: rgba(27,175,122,0.14); border-color: rgba(27,175,122,0.38); }
.chip-dense   { background: rgba(42,120,214,0.13); border-color: rgba(42,120,214,0.35); }
.chip-bm25    { background: rgba(237,161,0,0.16);  border-color: rgba(237,161,0,0.42); }
.chip-hybrid  { background: rgba(42,120,214,0.13); border-color: rgba(42,120,214,0.35); }
.chip-pageindex { background: rgba(232,123,164,0.15); border-color: rgba(232,123,164,0.42); }
.chip-none    { background: rgba(128,128,128,0.15); border-color: rgba(128,128,128,0.35); }
.chip-muted   { background: rgba(128,128,128,0.10); border-color: rgba(128,128,128,0.25); font-weight: 500; }

/* ---------- Citation trong câu trả lời ---------- */
.cite {
  display: inline-block; padding: 0 6px; margin: 0 1px; border-radius: 6px;
  font-size: 0.75em; font-weight: 700; vertical-align: 1px;
  background: rgba(42,120,214,0.16); border: 1px solid rgba(42,120,214,0.45);
}
.cite-missing { background: rgba(227,73,72,0.14); border-color: rgba(227,73,72,0.5); }

/* ---------- Thẻ nguồn ---------- */
.src-card {
  border: 1px solid rgba(128,128,128,0.28); border-radius: 12px;
  padding: 12px 14px; margin-bottom: 10px;
}
.src-card.cited { border-left: 4px solid #2a78d6; }
.src-card.uncited { opacity: 0.72; }
.src-head { display: flex; align-items: flex-start; gap: 8px; }
.src-tag {
  flex: none; font-weight: 800; font-size: 0.8rem; padding: 2px 7px; border-radius: 7px;
  background: rgba(42,120,214,0.16); border: 1px solid rgba(42,120,214,0.45);
}
.src-title { font-weight: 650; font-size: 0.93rem; line-height: 1.35; }
.src-title a { color: inherit; text-decoration: underline; text-decoration-color: rgba(128,128,128,0.5); }
.src-meta { display: flex; flex-wrap: wrap; gap: 6px; margin: 7px 0 8px; align-items: center; }
.src-snippet { font-size: 0.86rem; line-height: 1.55; opacity: 0.9; }
.src-snippet mark { background: rgba(237,161,0,0.30); color: inherit; padding: 0 2px; border-radius: 3px; }
.score { display: flex; align-items: center; gap: 8px; font-size: 0.76rem; opacity: 0.85; }
.score-track { width: 90px; height: 6px; border-radius: 999px; background: rgba(128,128,128,0.22); overflow: hidden; }
.score-fill { display: block; height: 100%; border-radius: 999px; background: #2a78d6; }

/* ---------- Trạng thái câu trả lời ---------- */
.answer-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; align-items: center; }
.refusal {
  border-radius: 12px; padding: 12px 14px;
  background: rgba(128,128,128,0.10); border: 1px dashed rgba(128,128,128,0.45);
}

/* ---------- Ô ví dụ ---------- */
.empty-state { text-align: center; padding: 28px 0 8px; opacity: 0.85; }
.empty-state .big { font-size: 2.8rem; color: #2a78d6; }
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def theme_type() -> str:
    """'light' hoặc 'dark' theo theme hiện tại của người xem."""
    try:
        return st.context.theme.type or "light"
    except Exception:
        return "light"


def icon(name: str) -> str:
    """HTML của một Material Symbol, dùng trong st.html (không hỗ trợ :material/...:)."""
    return f'<span class="msi">{name}</span>'


def hero(icon_name: str, title: str, subtitle: str) -> None:
    st.html(
        f'<div class="hero"><div class="hero-icon">{icon(icon_name)}</div>'
        f"<div><h1>{title}</h1><p>{subtitle}</p></div></div>"
    )
