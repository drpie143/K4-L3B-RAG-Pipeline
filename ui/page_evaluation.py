"""Trang Đánh giá: so sánh A/B dense-only với hybrid + RRF trên 4 metric RAGAS."""

import altair as alt
import pandas as pd
import streamlit as st

from . import backend
from .mock_data import METRICS
from .theme import SERIES_COLORS, hero, theme_type


METRIC_LABELS = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer relevance",
    "context_recall": "Context recall",
    "context_precision": "Context precision",
}
METRIC_HELP = {
    "faithfulness": "Câu trả lời có bám đúng nội dung các nguồn đã truy xuất không.",
    "answer_relevancy": "Câu trả lời có đúng trọng tâm câu hỏi không.",
    "context_recall": "Nguồn truy xuất có chứa đủ thông tin của đáp án chuẩn không.",
    "context_precision": "Các nguồn liên quan có được xếp ở thứ hạng cao không.",
}
STAGE_LABELS = {"retrieval": ":material/search: Retrieval", "generation": ":material/edit: Generation", "data": ":material/dataset: Dữ liệu"}


def _checklist(evaluation: dict, golden: list) -> None:
    result_md = backend.EVALUATION_DIR / "RESULT.md"
    todo_count = result_md.read_text(encoding="utf-8").count("TODO") if result_md.exists() else None
    items = [
        (len(golden) >= 15, f"Golden dataset ≥ 15 câu (hiện có {len(golden)})"),
        (not evaluation.get("is_sample"), "Có kết quả RAGAS thật (eval_results.json)"),
        (todo_count == 0, "RESULT.md không còn TODO" + (f" (còn {todo_count})" if todo_count else "")),
    ]
    done = sum(ok for ok, _ in items)
    with st.container(border=True):
        st.markdown(f"**Tiến độ phần đánh giá · {done}/{len(items)}**")
        st.progress(done / len(items))
        for ok, text in items:
            st.markdown(f"{':green[:material/check_circle:]' if ok else ':gray[:material/radio_button_unchecked:]'} {text}")


def _kpis(configs: dict) -> None:
    a, b = configs["A"]["overall"], configs["B"]["overall"]
    columns = st.columns(5)
    for column, metric in zip(columns, METRICS):
        column.metric(
            METRIC_LABELS[metric], f"{b[metric]:.2f}", f"{b[metric] - a[metric]:+.2f} so với A",
            help=METRIC_HELP[metric], border=True,
        )
    avg_a = sum(a.values()) / len(a)
    avg_b = sum(b.values()) / len(b)
    columns[4].metric("Trung bình", f"{avg_b:.2f}", f"{avg_b - avg_a:+.2f} so với A", border=True,
                      help="Trung bình 4 metric của Config B.")


def _comparison_chart(configs: dict) -> None:
    labels = {key: f"{key} · {configs[key]['label']}" for key in ("A", "B")}
    rows = [
        {"Metric": METRIC_LABELS[m], "Cấu hình": labels[key], "Điểm": configs[key]["overall"][m]}
        for m in METRICS for key in ("A", "B")
    ]
    data = pd.DataFrame(rows)
    colors = SERIES_COLORS["dark" if theme_type() == "dark" else "light"]
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Metric:N", sort=[METRIC_LABELS[m] for m in METRICS], title=None,
                    scale=alt.Scale(paddingInner=0.4, paddingOuter=0.2),
                    axis=alt.Axis(labelAngle=0, labelFontSize=12)),
            xOffset=alt.XOffset("Cấu hình:N", sort=list(labels.values()),
                                scale=alt.Scale(paddingInner=0.08)),
            y=alt.Y("Điểm:Q", scale=alt.Scale(domain=[0, 1]), title="Điểm (0–1)",
                    axis=alt.Axis(gridOpacity=0.35, tickCount=5)),
            color=alt.Color("Cấu hình:N", sort=list(labels.values()),
                            scale=alt.Scale(domain=list(labels.values()), range=colors),
                            legend=alt.Legend(orient="top", title=None)),
            tooltip=["Metric", "Cấu hình", alt.Tooltip("Điểm:Q", format=".2f")],
        )
        .properties(height=320)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, width="stretch")
    with st.expander("Bảng số liệu"):
        table = data.pivot(index="Metric", columns="Cấu hình", values="Điểm").reindex(
            [METRIC_LABELS[m] for m in METRICS])
        table["Chênh lệch B − A"] = table[labels["B"]] - table[labels["A"]]
        st.dataframe(table.style.format("{:+.2f}", subset=["Chênh lệch B − A"]).format(
            "{:.2f}", subset=list(labels.values())), width="stretch")


def _latency(configs: dict) -> None:
    a = configs["A"].get("avg_latency_ms")
    b = configs["B"].get("avg_latency_ms")
    if a is None or b is None:
        return
    left, right = st.columns(2)
    left.metric(f":material/timer: Độ trễ TB · A {configs['A']['label']}", f"{a / 1000:.2f}s", border=True)
    right.metric(f":material/timer: Độ trễ TB · B {configs['B']['label']}", f"{b / 1000:.2f}s",
                 f"{(b - a) / 1000:+.2f}s", delta_color="inverse", border=True)


def _per_question(evaluation: dict) -> None:
    rows = evaluation.get("per_question") or []
    if not rows:
        st.info("Chưa có kết quả theo từng câu hỏi.")
        return
    data = pd.DataFrame(rows)
    data["Trung bình"] = data[METRICS].mean(axis=1)

    choice = st.segmented_control("Lọc cấu hình", ["Tất cả", "A", "B"], default="Tất cả",
                                  key="eval_config_filter") or "Tất cả"
    if choice != "Tất cả":
        data = data[data["config"] == choice]
    data = data.sort_values("Trung bình")

    progress = {
        metric: st.column_config.ProgressColumn(METRIC_LABELS.get(metric, metric), min_value=0, max_value=1,
                                                format="%.2f", width="small")
        for metric in METRICS + ["Trung bình"]
    }
    st.dataframe(
        data[["question", "config", *METRICS, "Trung bình", "failure_stage", "root_cause"]],
        hide_index=True,
        width="stretch",
        column_config={
            "question": st.column_config.TextColumn("Câu hỏi", width="large"),
            "config": st.column_config.TextColumn("Cấu hình", width="small"),
            "failure_stage": st.column_config.TextColumn("Lỗi ở bước"),
            "root_cause": st.column_config.TextColumn("Nguyên nhân", width="medium"),
            **progress,
        },
    )

    st.markdown("##### :material/trending_down: 3 câu trả lời kém nhất")
    for _, row in data.head(3).iterrows():
        with st.container(border=True):
            stage = STAGE_LABELS.get(row.get("failure_stage") or "", "—")
            st.markdown(f"**{row['question']}**  \nCấu hình **{row['config']}** · điểm TB **{row['Trung bình']:.2f}** · {stage}")
            if row.get("root_cause"):
                st.caption(f"Nguyên nhân: {row['root_cause']}")


def _golden(golden: list, error: str | None) -> None:
    if error:
        st.warning(error, icon=":material/edit_note:")
        st.caption("Định dạng mong đợi của `group_project/evaluation/golden_dataset.json`:")
        st.code('[\n  {\n    "question": "...",\n    "expected_answer": "...",\n'
                '    "expected_context": "..."\n  }\n]', language="json")
        return
    st.progress(min(len(golden) / 15, 1.0), text=f"{len(golden)}/15 câu tối thiểu")
    st.dataframe(
        pd.DataFrame(golden), hide_index=True, width="stretch",
        column_config={
            "question": st.column_config.TextColumn("Câu hỏi", width="medium"),
            "expected_answer": st.column_config.TextColumn("Đáp án chuẩn", width="large"),
            "expected_context": st.column_config.TextColumn("Ngữ cảnh chuẩn", width="large"),
        },
    )


def evaluation_page() -> None:
    hero("monitoring", "Đánh giá RAG · A/B", "So sánh Dense-only (A) với Hybrid + RRF (B) trên 4 metric RAGAS")

    evaluation = backend.load_evaluation()
    golden, golden_error = backend.load_golden()
    configs = evaluation["configs"]

    if evaluation.get("is_sample"):
        st.info(
            "Đang hiển thị **dữ liệu minh họa**. Khi chạy xong RAGAS, ghi kết quả vào "
            "`group_project/evaluation/eval_results.json` (cùng cấu trúc dữ liệu mẫu), trang sẽ tự cập nhật.",
            icon=":material/science:",
        )

    left, right = st.columns([2.2, 1])
    with left:
        info = evaluation.get("run_info", {})
        with st.container(border=True):
            st.markdown("**Thông tin lượt chạy**")
            c1, c2, c3 = st.columns(3)
            c1.caption(f"Ngày: **{info.get('evaluation_date', '—')}**  \nFramework: **{info.get('framework', '—')}**")
            c2.caption(f"Generator: **{info.get('generator_model', '—')}**  \nEvaluator: **{info.get('evaluator_model', '—')}**")
            c3.caption(f"Embedding: **{info.get('embedding_model', '—')}**  \ntop-k: **{info.get('top_k', '—')}** · "
                       f"threshold: **{info.get('score_threshold', '—')}**")
    with right:
        _checklist(evaluation, golden)

    st.markdown("#### Điểm tổng quan · Config B so với A")
    _kpis(configs)
    _comparison_chart(configs)
    _latency(configs)

    tab_questions, tab_golden = st.tabs([":material/quiz: Theo từng câu hỏi", ":material/fact_check: Golden dataset"])
    with tab_questions:
        _per_question(evaluation)
    with tab_golden:
        _golden(golden, golden_error)
