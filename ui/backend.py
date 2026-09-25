"""Lớp kết nối giữa giao diện và backend RAG.

Giao diện CHỈ gọi các hàm trong file này. Khi backend hoàn thành, người làm
backend không cần sửa code UI, chỉ cần đảm bảo:

1. Chat: `src.task10_generation.generate_with_citation(query, top_k)` trả về
   GenerationResult đúng docs/MODULE_CONTRACTS.md. Nếu hàm nhận thêm tham số
   `use_reranking` thì nút chuyển Dense-only / Hybrid trên UI sẽ có tác dụng.
2. Evaluation: ghi kết quả RAGAS vào `group_project/evaluation/eval_results.json`
   theo schema của `ui.mock_data.MOCK_EVALUATION` (bỏ khóa "is_sample").
3. Golden dataset: `group_project/evaluation/golden_dataset.json` là list các
   object có `question`, `expected_answer`, `expected_context`.

Biến môi trường RAG_UI_MODE: "auto" (mặc định: thử backend thật, chưa cài
đặt thì dùng demo), "demo" (luôn dùng dữ liệu mẫu), "real" (luôn gọi backend).
"""

import inspect
import json
import os
import time
from pathlib import Path

from . import mock_data


ROOT = Path(__file__).parent.parent
STANDARDIZED_DIR = ROOT / "data" / "standardized"
EVALUATION_DIR = ROOT / "group_project" / "evaluation"
EVAL_RESULTS_PATH = EVALUATION_DIR / "eval_results.json"
GOLDEN_PATH = EVALUATION_DIR / "golden_dataset.json"

UI_MODE = os.getenv("RAG_UI_MODE", "auto").lower()

# Ghi nhớ khi backend thật chưa được cài đặt (NotImplementedError) để khỏi gọi lại.
_backend_ready: bool | None = None if UI_MODE == "auto" else UI_MODE == "real"


def backend_mode() -> str:
    """'real', 'demo' hoặc 'unknown' (auto, chưa gọi lần nào)."""
    if _backend_ready is None:
        return "unknown"
    return "real" if _backend_ready else "demo"


def supports_retrieval_toggle() -> bool:
    """Backend có nhận tham số use_reranking hay không."""
    if backend_mode() != "real":
        return True
    try:
        from src.task10_generation import generate_with_citation

        return "use_reranking" in inspect.signature(generate_with_citation).parameters
    except Exception:
        return False


def ask(query: str, top_k: int = 5, use_reranking: bool = True) -> dict:
    """Trả về GenerationResult kèm `latency_ms` và `mode` ('real' | 'demo')."""
    global _backend_ready
    started = time.perf_counter()

    result = None
    if _backend_ready is not False:
        try:
            from src.task10_generation import generate_with_citation

            kwargs = {"top_k": top_k}
            if "use_reranking" in inspect.signature(generate_with_citation).parameters:
                kwargs["use_reranking"] = use_reranking
            result = generate_with_citation(query, **kwargs)
            _backend_ready = True
        except NotImplementedError:
            if UI_MODE == "real":
                raise
            _backend_ready = False

    mode = "real"
    if result is None:
        result = _mock_answer(query, use_reranking)
        mode = "demo"

    return {**result, "latency_ms": (time.perf_counter() - started) * 1000, "mode": mode}


def contract_problem(result: dict) -> str | None:
    """Mô tả lỗi schema (nếu có) để hiển thị trong phần chẩn đoán."""
    from src.contracts import validate_generation_result

    clean = {key: result[key] for key in ("answer", "sources", "retrieval_source") if key in result}
    try:
        validate_generation_result(clean)
    except ValueError as error:
        return str(error)
    return None


def _mock_answer(query: str, use_reranking: bool) -> dict:
    time.sleep(0.7)  # mô phỏng độ trễ để thấy trạng thái đang xử lý
    normalized = " ".join(query.lower().split())
    for question, answer in mock_data.MOCK_ANSWERS.items():
        if normalized == " ".join(question.lower().split()):
            return _with_method(answer, use_reranking)
    if any(keyword in normalized for keyword in mock_data.IN_DOMAIN_KEYWORDS):
        generic = mock_data.MOCK_ANSWERS[mock_data.EXAMPLE_QUESTIONS[0]]
        return _with_method({
            **generic,
            "answer": (
                "*(Chế độ demo: backend chưa sẵn sàng nên đây là câu trả lời mẫu.)*\n\n" + generic["answer"]
            ),
        }, use_reranking)
    return dict(mock_data.REFUSAL_RESULT)


def _with_method(result: dict, use_reranking: bool) -> dict:
    """Giả lập Dense-only: đổi nhãn nguồn hybrid thành dense để UI hiển thị đúng."""
    if use_reranking or result["retrieval_source"] != "hybrid":
        return result
    sources = [
        {**source, "retrieval_method": "dense", "score": round(0.78 - 0.07 * index, 2)}
        for index, source in enumerate(result["sources"])
    ]
    return {**result, "sources": sources}


# ---------------------------------------------------------------- Corpus
def _parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    metadata = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        try:
            metadata[key.strip()] = json.loads(value)
        except ValueError:
            metadata[key.strip()] = value.strip("\"'")
    return metadata, text[end + 5:]


def load_corpus() -> list[dict]:
    """Danh sách tài liệu đã chuẩn hóa (đọc front matter của từng file .md)."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        metadata, body = _parse_front_matter(path.read_text(encoding="utf-8"))
        documents.append({
            "path": path,
            "title": metadata.get("title") or path.stem,
            "doc_type": metadata.get("doc_type") or path.parent.name,
            "source": metadata.get("source") or path.name,
            "url": metadata.get("url"),
            "number": metadata.get("number"),
            "issued": metadata.get("issued"),
            "effective": metadata.get("effective"),
            "published": (metadata.get("date_published") or "")[:10] or None,
            "chars": len(body),
            "articles": body.count("\n### Điều "),
            "body": body,
        })
    return documents


# ---------------------------------------------------------------- Evaluation
def load_evaluation() -> dict:
    """Kết quả evaluation thật nếu có, ngược lại trả dữ liệu mẫu (is_sample=True)."""
    if EVAL_RESULTS_PATH.exists():
        try:
            data = json.loads(EVAL_RESULTS_PATH.read_text(encoding="utf-8"))
            return {**data, "is_sample": False}
        except ValueError:
            pass
    return mock_data.MOCK_EVALUATION


def load_golden() -> tuple[list[dict], str | None]:
    """(dataset, lỗi). Dataset rỗng nếu file chưa có hoặc sai định dạng."""
    if not GOLDEN_PATH.exists() or not GOLDEN_PATH.read_text(encoding="utf-8").strip():
        return [], "Chưa có golden dataset (file trống)."
    try:
        data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    except ValueError as error:
        return [], f"File JSON không hợp lệ: {error}"
    if not isinstance(data, list):
        return [], "Golden dataset phải là một list."
    return data, None
