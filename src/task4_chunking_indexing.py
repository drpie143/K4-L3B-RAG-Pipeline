"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

from .contracts import validate_document


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Văn bản pháp luật và bài báo đã có Markdown heading rõ ràng. Chunk theo
# Chương/Mục/Điều/section, chỉ tách tiếp theo đoạn hoặc câu khi section quá dài.
# Heading path được lặp lại để mỗi chunk tự mang đủ ngữ cảnh; nội dung không overlap.
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 0
CHUNKING_METHOD = "markdown_hierarchy"
EMBEDDING_BATCH_SIZE = 32

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"

_LOCAL_EMBEDDING_MODEL = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed văn bản bằng provider được chọn trong .env."""
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("texts must contain non-empty strings")

    provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").lower()
    if provider == "sentence_transformers":
        from sentence_transformers import SentenceTransformer

        global _LOCAL_EMBEDDING_MODEL
        if _LOCAL_EMBEDDING_MODEL is None:
            _LOCAL_EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL)
        vectors = _LOCAL_EMBEDDING_MODEL.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()
    if provider == "openai":
        from openai import OpenAI

        response = OpenAI().embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]
    if provider == "gemini":
        from google import genai

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
        return [item.values for item in response.embeddings]
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            continue
        metadata, content = _parse_front_matter(raw)
        relative_path = path.relative_to(STANDARDIZED_DIR)
        source_metadata = {
            key: value
            for key, value in metadata.items()
            if value not in (None, "")
        }
        document = {
            "id": relative_path.with_suffix("").as_posix(),
            "content": content.strip(),
            "metadata": {
                **source_metadata,
                "source": metadata.get("source") or path.name,
                "title": metadata.get("title") or path.stem.replace("_", " "),
                "doc_type": metadata.get("doc_type") or relative_path.parts[0],
                "url": metadata.get("url") or None,
            },
        }
        validate_document(document)
        documents.append(document)
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chunk theo cấu trúc Markdown, không dùng sliding-window overlap."""
    chunks = []
    for document in documents:
        validate_document(document)
        sections = _split_markdown_hierarchy(document["content"])
        for index, section in enumerate(sections):
            text = section["content"]
            chunk_metadata = {
                **document["metadata"],
                "chunk_index": index,
                "chunking_method": CHUNKING_METHOD,
            }
            if section["heading_path"]:
                chunk_metadata["heading_path"] = section["heading_path"]
                chunk_metadata["section"] = section["section"]
            if section["part"] > 1:
                chunk_metadata["section_part"] = section["part"]
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": chunk_metadata,
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = []
    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[start : start + EMBEDDING_BATCH_SIZE]
        vectors.extend(embed_texts([chunk["content"] for chunk in batch]))
    if len(vectors) != len(chunks):
        raise ValueError("embedding provider returned an unexpected vector count")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return
    for chunk in chunks:
        validate_document(chunk, require_chunk=True)
        if "embedding" not in chunk:
            raise ValueError(f"chunk {chunk['id']} has no embedding")
    collection = get_collection()
    current_ids = {chunk["id"] for chunk in chunks}
    existing_ids = set(collection.get(include=[]).get("ids", []))
    stale_ids = sorted(existing_ids - current_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)

    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[
            {key: ("" if value is None else value) for key, value in chunk["metadata"].items()}
            for chunk in chunks
        ],
    )


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Parse YAML front matter dạng key/value mà không thêm dependency."""
    if not text.startswith("---\n"):
        return {}, text
    marker = text.find("\n---\n", 4)
    if marker == -1:
        return {}, text
    metadata = {}
    for line in text[4:marker].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, text[marker + 5 :]


HEADING_PATTERN = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?;:])\s+(?=[A-ZÀ-ỸĐ0-9])")


def _split_markdown_hierarchy(text: str) -> list[dict]:
    """Tách Markdown theo heading path rồi chia section dài mà không overlap."""
    heading_stack: dict[int, str] = {}
    current_body: list[str] = []
    current_path: list[str] = []
    sections: list[tuple[list[str], str]] = []

    def flush() -> None:
        body = "\n".join(current_body).strip()
        if body:
            sections.append((list(current_path), body))

    for line in text.splitlines():
        heading = HEADING_PATTERN.match(line)
        if heading:
            flush()
            current_body = []
            level = len(heading.group(1))
            title = heading.group(2).strip()
            for old_level in [item for item in heading_stack if item >= level]:
                del heading_stack[old_level]
            heading_stack[level] = title
            current_path = [heading_stack[item] for item in sorted(heading_stack)]
        else:
            current_body.append(line)
    flush()

    # Tài liệu không có heading vẫn được chia theo đoạn/câu.
    if not sections and text.strip():
        sections = [([], text.strip())]

    chunks = []
    for heading_path, body in sections:
        prefix = _heading_prefix(heading_path)
        body_parts = _split_section_body(body, max(CHUNK_SIZE - len(prefix) - 2, 200))
        path_label = " > ".join(heading_path)
        for part_number, body_part in enumerate(body_parts, 1):
            content = f"{prefix}\n\n{body_part}".strip() if prefix else body_part
            chunks.append({
                "content": content,
                "heading_path": path_label,
                "section": heading_path[-1] if heading_path else "",
                "part": part_number,
            })
    return chunks


def _heading_prefix(heading_path: list[str]) -> str:
    """Khôi phục hierarchy với heading levels ổn định trong từng chunk."""
    return "\n\n".join(
        f"{'#' * min(index, 4)} {title}"
        for index, title in enumerate(heading_path, 1)
    )


def _split_section_body(body: str, budget: int) -> list[str]:
    """Pack đoạn văn trong budget; đoạn dài được tách theo câu rồi từ."""
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()]
    units = []
    for paragraph in paragraphs:
        if len(paragraph) <= budget:
            units.append(paragraph)
            continue
        sentences = [item.strip() for item in SENTENCE_BOUNDARY.split(paragraph) if item.strip()]
        for sentence in sentences:
            units.extend(_hard_split(sentence, budget))

    packed = []
    current = ""
    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit
        if current and len(candidate) > budget:
            packed.append(current)
            current = unit
        else:
            current = candidate
    if current:
        packed.append(current)
    return packed or [body[:budget].strip()]


def _hard_split(text: str, budget: int) -> list[str]:
    """Tách một câu cực dài theo từ, không lặp nội dung."""
    if len(text) <= budget:
        return [text]
    parts = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if current and len(candidate) > budget:
            parts.append(current)
            current = word
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
