"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

import requests
from dotenv import load_dotenv
from pageindex import PageIndexClient

from .contracts import validate_search_results
from .task4_chunking_indexing import load_documents


load_dotenv()

DOC_ID_CACHE = Path(__file__).parent.parent / "pageindex_doc_ids.json"
PDF_DIR = Path(__file__).parent.parent / "pageindex_pdfs"
HTTP_TIMEOUT_SECONDS = float(os.getenv("PAGEINDEX_HTTP_TIMEOUT", "60"))
HTTP_RETRIES = int(os.getenv("PAGEINDEX_HTTP_RETRIES", "3"))
POLL_TIMEOUT_SECONDS = float(os.getenv("PAGEINDEX_POLL_TIMEOUT", "600"))
POLL_INTERVAL_SECONDS = float(os.getenv("PAGEINDEX_POLL_INTERVAL", "3"))
_FONT_CANDIDATES = (
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
PDF_RENDERER_VERSION = "2"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    documents = load_documents()
    cache = _load_cache()
    client = _client()
    changed = False

    for document in documents:
        digest = _document_digest(document)
        cached = cache.get(document["id"])
        if isinstance(cached, dict) and cached.get("sha256") == digest and cached.get("doc_id"):
            continue

        pdf_path = _pdf_path(document["id"])
        _write_pdf(_pdf_text(document), pdf_path)
        with _http_timeout(HTTP_TIMEOUT_SECONDS):
            response = client.submit_document(str(pdf_path))
        doc_id = response.get("doc_id") or response.get("id")
        if not isinstance(doc_id, str) or not doc_id.strip():
            raise RuntimeError(f"PageIndex did not return a doc_id for {document['id']}")
        cache[document["id"]] = {
            "doc_id": doc_id,
            "sha256": digest,
            "source": document["metadata"]["source"],
            "title": document["metadata"]["title"],
            "doc_type": document["metadata"]["doc_type"],
            "url": document["metadata"]["url"],
        }
        changed = True

    if changed or not DOC_ID_CACHE.exists():
        _save_cache(cache)


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []

    upload_documents()
    client = _client()
    documents = load_documents()
    cache = _load_cache()
    results: list[dict] = []
    errors: list[Exception] = []

    for document in documents:
        entry = cache.get(document["id"])
        if not isinstance(entry, dict) or not entry.get("doc_id"):
            continue
        try:
            results.extend(_search_document(client, entry, document["id"], query))
        except Exception as exc:
            errors.append(exc)

    if not results and errors:
        raise errors[0]

    ranked = _dedupe_and_rank(results, top_k)
    validate_search_results(ranked, top_k=top_k, expected_method="pageindex")
    return ranked


def _client() -> PageIndexClient:
    load_dotenv()
    api_key = os.getenv("PAGEINDEX_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PAGEINDEX_API_KEY is not set")
    return PageIndexClient(api_key=api_key)


def _search_document(client: PageIndexClient, entry: dict, document_id: str, query: str) -> list[dict]:
    doc_id = entry["doc_id"]
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while True:
        with _http_timeout(HTTP_TIMEOUT_SECONDS):
            ready = client.is_retrieval_ready(doc_id)
        if ready:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError(f"PageIndex document {doc_id} was not retrieval-ready")
        time.sleep(POLL_INTERVAL_SECONDS)

    with _http_timeout(HTTP_TIMEOUT_SECONDS):
        submitted = client.submit_query(doc_id, query)
    retrieval_id = submitted.get("retrieval_id")
    if not isinstance(retrieval_id, str) or not retrieval_id.strip():
        raise RuntimeError(f"PageIndex did not return a retrieval_id for {document_id}")

    payload = _wait_for_retrieval(client, retrieval_id, time.monotonic() + POLL_TIMEOUT_SECONDS)
    parsed = []
    for index, node in enumerate(_retrieved_nodes(payload)):
        content, page_index = _node_content(node)
        if not content:
            continue
        node_id = node.get("node_id") or node.get("id") or index
        chunk_index = page_index if isinstance(page_index, int) and page_index >= 0 else index
        parsed.append({
            "id": f"{document_id}::pageindex-{node_id}",
            "content": content,
            "score": _node_score(node),
            "metadata": {
                "source": entry["source"],
                "title": entry["title"],
                "doc_type": entry["doc_type"],
                "url": entry.get("url"),
                "chunk_index": chunk_index,
            },
            "retrieval_method": "pageindex",
        })
    return parsed


def _wait_for_retrieval(client: PageIndexClient, retrieval_id: str, deadline: float) -> dict:
    pending = {"processing", "pending", "queued", "running", "in_progress"}
    finished = {"completed", "complete", "success", "succeeded", "done"}
    while True:
        with _http_timeout(HTTP_TIMEOUT_SECONDS):
            payload = client.get_retrieval(retrieval_id)
        status = str(payload.get("status", "")).lower()
        if status in {"failed", "error"}:
            message = payload.get("error") or payload.get("message") or "PageIndex retrieval failed"
            raise RuntimeError(str(message))
        if status in finished or (status not in pending and (status or _retrieved_nodes(payload))):
            return payload
        if time.monotonic() >= deadline:
            raise TimeoutError(f"PageIndex retrieval {retrieval_id} timed out")
        time.sleep(POLL_INTERVAL_SECONDS)


def _retrieved_nodes(payload: dict) -> list:
    if not isinstance(payload, dict):
        return []
    for key in ("retrieved_nodes", "nodes"):
        nodes = payload.get(key)
        if isinstance(nodes, list):
            return nodes
    result = payload.get("result")
    if isinstance(result, dict):
        nodes = result.get("retrieved_nodes") or result.get("nodes")
        if isinstance(nodes, list):
            return nodes
    if isinstance(result, list):
        return result
    return []


def _node_content(node: dict) -> tuple[str, int | None]:
    if not isinstance(node, dict):
        return "", None
    snippets = node.get("relevant_contents")
    if snippets is None:
        snippets = node.get("relevant_content")
    parts: list[str] = []
    page_index = node.get("page_index") if isinstance(node.get("page_index"), int) else None
    def collect(value) -> None:
        nonlocal page_index
        if isinstance(value, str):
            if value.strip():
                parts.append(value.strip())
            return
        if isinstance(value, list):
            for item in value:
                collect(item)
            return
        if not isinstance(value, dict):
            return

        text = value.get("relevant_content") or value.get("content") or value.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
        elif isinstance(text, (list, dict)):
            collect(text)

        if page_index is None and isinstance(value.get("page_index"), int):
            page_index = value["page_index"]
        physical_index = value.get("physical_index")
        if page_index is None and isinstance(physical_index, str):
            digits = "".join(character for character in physical_index if character.isdigit())
            if digits:
                page_index = int(digits)

    collect(snippets)
    if not parts:
        for key in ("text", "content", "summary"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
                break
    title = node.get("title")
    content = "\n".join(parts).strip()
    if isinstance(title, str) and title.strip() and title.strip() not in content:
        content = f"{title.strip()}\n{content}".strip()
    return content, page_index


def _node_score(node: dict) -> float | None:
    score = node.get("score") if isinstance(node, dict) else None
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    return float(score)


def _dedupe_and_rank(results: list[dict], top_k: int) -> list[dict]:
    ranked: list[dict] = []
    seen: set[str] = set()
    scored = [item for item in results if item["score"] is not None]
    if not scored:
        total = len(results)
        for index, item in enumerate(results):
            item["score"] = float(total - index)
    else:
        for item in results:
            if item["score"] is None:
                item["score"] = 0.0
    for item in sorted(results, key=lambda result: (-float(result["score"]), result["id"])):
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        ranked.append(item)
        if len(ranked) >= top_k:
            break
    return ranked


def _document_digest(document: dict) -> str:
    metadata = document["metadata"]
    payload = "\n".join([
        PDF_RENDERER_VERSION,
        metadata["source"],
        metadata["title"],
        metadata["doc_type"],
        metadata["url"] or "",
        document["content"],
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pdf_text(document: dict) -> str:
    metadata = document["metadata"]
    return f"{metadata['title']}\n\n{document['content']}".replace("\x00", "")


def _pdf_path(document_id: str) -> Path:
    safe_name = document_id.replace("/", "__").replace("\\", "__")
    return PDF_DIR / f"{safe_name}.pdf"


def _write_pdf(text: str, dest: Path) -> None:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    font = next((path for path in _FONT_CANDIDATES if path.is_file()), None)
    if font is None:
        raise RuntimeError("No Unicode font available to convert Markdown into a PageIndex PDF")

    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("Body", "", str(font))
    pdf.set_font("Body", size=11)
    for paragraph in text.splitlines() or [text]:
        pdf.multi_cell(
            pdf.epw,
            6,
            paragraph if paragraph else " ",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            wrapmode="CHAR",
        )
    pdf.output(str(dest))


def _load_cache() -> dict:
    if not DOC_ID_CACHE.is_file():
        return {}
    try:
        payload = json.loads(DOC_ID_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_cache(cache: dict) -> None:
    temporary = DOC_ID_CACHE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(DOC_ID_CACHE)


@contextmanager
def _http_timeout(seconds: float):
    """Gắn timeout và retry GET/HEAD vì SDK 0.2 chưa hỗ trợ hai cơ chế này."""
    original = requests.sessions.Session.request

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", seconds)
        attempts = HTTP_RETRIES + 1 if str(method).upper() in {"GET", "HEAD"} else 1
        for attempt in range(attempts):
            try:
                return original(self, method, url, **kwargs)
            except requests.RequestException:
                if attempt + 1 >= attempts:
                    raise
                time.sleep(min(2 ** attempt, 8))
        raise RuntimeError("Unreachable PageIndex retry state")

    requests.sessions.Session.request = request
    try:
        yield
    finally:
        requests.sessions.Session.request = original


if __name__ == "__main__":
    upload_documents()
