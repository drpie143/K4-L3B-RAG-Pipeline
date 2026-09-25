"""Các thành phần hiển thị: câu trả lời có citation, thẻ nguồn, chip trạng thái."""

import html
import re

import streamlit as st

from .theme import icon


DOC_TYPE_LABELS = {"legal": ("gavel", "Văn bản pháp luật"), "news": ("newspaper", "Bài viết")}
METHOD_LABELS = {
    "dense": ("Dense", "cosine"),
    "bm25": ("BM25", "BM25"),
    "hybrid": ("Hybrid · RRF", "RRF"),
    "pageindex": ("PageIndex", "score"),
}
SOURCE_LABELS = {
    "hybrid": ("merge", "Hybrid + RRF"),
    "dense": ("my_location", "Dense-only"),
    "pageindex": ("account_tree", "Fallback PageIndex"),
    "none": ("block", "Không đủ bằng chứng"),
}

CITATION = re.compile(r"\[(S\d+(?:\s*[,;]\s*S\d+)*)\]")
STOPWORDS = {
    "của", "và", "các", "cho", "không", "được", "với", "nào", "bao", "nhiêu", "thì", "là", "có",
    "những", "như", "thế", "này", "khi", "phải", "theo", "trong", "một", "người", "hay", "hoặc",
}


def chip(text: str, kind: str = "muted", title: str = "") -> str:
    tooltip = f' title="{html.escape(title)}"' if title else ""
    return f'<span class="chip chip-{kind}"{tooltip}>{text}</span>'


def cited_indices(answer: str) -> set[int]:
    """Các số thứ tự nguồn (1-based) được nhắc tới trong câu trả lời."""
    found = set()
    for group in CITATION.findall(answer):
        found.update(int(tag.strip()[1:]) for tag in re.split(r"[,;]", group))
    return found


def _answer_html(answer: str, source_count: int) -> str:
    """Escape HTML từ LLM rồi thay [S1] thành pill; pill đỏ nếu không có nguồn tương ứng."""
    safe = answer.replace("<", "&lt;").replace(">", "&gt;")

    def replace(match: re.Match) -> str:
        pills = []
        for tag in re.split(r"[,;]", match.group(1)):
            number = int(tag.strip()[1:])
            missing = number < 1 or number > source_count
            css = "cite cite-missing" if missing else "cite"
            hint = "Không tìm thấy nguồn này" if missing else f"Xem nguồn S{number} bên dưới"
            pills.append(f'<span class="{css}" title="{hint}">S{number}</span>')
        return "".join(pills)

    return CITATION.sub(replace, safe)


def _query_terms(query: str) -> list[str]:
    """Cụm từ để tô sáng: cụm 2–3 âm tiết liền nhau (tiếng Việt ghép từ âm tiết),
    cộng các từ viết tắt/số hiệu (GTGT, 141/2026). Âm tiết đơn lẻ bị bỏ vì quá nhiễu."""
    terms = set(re.findall(r"\b(?:[A-ZĐ]{2,}|\d+(?:/\d+)+)\b", query))
    marked = re.sub(r"\b(?:%s)\b" % "|".join(STOPWORDS), "|", query.lower())
    for chunk in re.split(r"[^\w\s/]+|\|", marked):
        syllables = chunk.split()
        for size in (3, 2):
            terms.update(" ".join(syllables[i:i + size]) for i in range(len(syllables) - size + 1))
    return sorted((t for t in terms if len(t) >= 3), key=len, reverse=True)


def _highlight(text: str, query: str) -> str:
    """Tô sáng cụm từ của câu hỏi xuất hiện trong đoạn trích (bonus: source highlighting)."""
    escaped = html.escape(text)
    terms = _query_terms(query)
    if not terms:
        return escaped
    pattern = re.compile(r"(?<!\w)(" + "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in terms) + r")(?!\w)", re.I)
    return pattern.sub(r"<mark>\1</mark>", escaped)


def _score_html(source: dict, max_score: float) -> str:
    method = source.get("retrieval_method", "")
    _, unit = METHOD_LABELS.get(method, (method, "score"))
    score = float(source.get("score") or 0)
    width = 100 * score / max_score if max_score > 0 else 0
    value = f"{score:.4f}" if method == "hybrid" else f"{score:.3f}" if score < 10 else f"{score:.1f}"
    return (
        f'<span class="score" title="Thanh điểm so với nguồn có điểm cao nhất trong lượt trả lời này">'
        f'<span class="score-track"><span class="score-fill" style="width:{width:.0f}%"></span></span>'
        f"{unit} {value}</span>"
    )


def source_card(index: int, source: dict, query: str, cited: bool, max_score: float) -> str:
    metadata = source.get("metadata", {})
    icon_name, type_label = DOC_TYPE_LABELS.get(metadata.get("doc_type"), ("description", metadata.get("doc_type", "")))
    method_label, _ = METHOD_LABELS.get(source.get("retrieval_method"), (source.get("retrieval_method"), ""))
    title = html.escape(metadata.get("title") or metadata.get("source") or "Không rõ tiêu đề")
    url = metadata.get("url")
    title_html = f'<a href="{html.escape(url)}" target="_blank">{title}</a>' if url else title

    content = source.get("content", "")
    preview = content if len(content) <= 320 else content[:320].rsplit(" ", 1)[0] + "…"
    full = ""
    if len(content) > 320:
        full = (
            f'<details><summary style="cursor:pointer;font-size:0.8rem;opacity:0.8">Xem toàn bộ đoạn trích</summary>'
            f'<div class="src-snippet" style="margin-top:6px">{_highlight(content, query)}</div></details>'
        )

    chips = [
        chip(f"{icon(icon_name)} {type_label}", metadata.get("doc_type", "muted")),
        chip(method_label, source.get("retrieval_method", "muted")),
        chip(f"chunk #{metadata.get('chunk_index', '—')}", "muted", source.get("id", "")),
    ]
    if cited:
        chips.append(chip(f"{icon('check')} Được trích dẫn", "news"))
    return (
        f'<div class="src-card {"cited" if cited else "uncited"}">'
        f'<div class="src-head"><span class="src-tag">S{index}</span><div class="src-title">{title_html}</div></div>'
        f'<div class="src-meta">{"".join(chips)}{_score_html(source, max_score)}</div>'
        f'<div class="src-snippet">{_highlight(preview, query)}</div>{full}</div>'
    )


def render_sources(sources: list[dict], answer: str, query: str, expanded: bool) -> None:
    if not sources:
        return
    cited = cited_indices(answer)
    max_score = max(float(s.get("score") or 0) for s in sources)
    used = sum(1 for i in range(1, len(sources) + 1) if i in cited)
    label = f":material/menu_book: Nguồn tham khảo · {len(sources)} đoạn · {used} được trích dẫn"
    with st.expander(label, expanded=expanded):
        st.html("".join(
            source_card(index, source, query, index in cited, max_score)
            for index, source in enumerate(sources, 1)
        ))


def render_answer(message: dict, expanded: bool) -> None:
    """Hiển thị một câu trả lời của trợ lý đã lưu trong session state."""
    sources = message.get("sources", [])
    retrieval_source = message.get("retrieval_source", "none")

    if message.get("error"):
        st.error(message["content"], icon=":material/error:")
        return
    if retrieval_source == "none" or not sources:
        st.html(
            f'<div class="refusal">{icon("block")} <b>Không đủ bằng chứng để trả lời.</b><br>'
            f'<span style="opacity:0.8">{html.escape(message["content"])}</span><br>'
            '<span style="opacity:0.65;font-size:0.85rem">Câu hỏi có thể nằm ngoài phạm vi tài liệu '
            "về pháp luật cho hộ kinh doanh. Hãy thử hỏi về đăng ký, thuế, hóa đơn hoặc kinh doanh trên sàn TMĐT."
            "</span></div>"
        )
    else:
        st.markdown(_answer_html(message["content"], len(sources)), unsafe_allow_html=True)

    icon_name, label = SOURCE_LABELS.get(retrieval_source, ("help", retrieval_source))
    meta = [chip(f"{icon(icon_name)} {label}", retrieval_source)]
    if message.get("latency_ms") is not None:
        meta.append(chip(f"{icon('timer')} {message['latency_ms'] / 1000:.1f}s", "muted"))
    if message.get("top_k"):
        meta.append(chip(f"top-k {message['top_k']}", "muted"))
    if message.get("mode") == "demo":
        meta.append(chip(f"{icon('science')} Dữ liệu demo", "bm25", "Backend chưa sẵn sàng, đây là câu trả lời mẫu"))
    missing = [n for n in cited_indices(message["content"]) if n > len(sources)]
    if missing:
        meta.append(chip(f"{icon('warning')} Citation không khớp: {', '.join(f'S{n}' for n in sorted(missing))}", "none"))
    st.html(f'<div class="answer-meta">{"".join(meta)}</div>')

    render_sources(sources, message["content"], message.get("query", ""), expanded)
