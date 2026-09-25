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
from pathlib import Path

from dotenv import load_dotenv

from .contracts import validate_document


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

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
        document = {
            "id": relative_path.with_suffix("").as_posix(),
            "content": content.strip(),
            "metadata": {
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
    """Chia Document thành chunks có id và chunk_index."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        split_text = splitter.split_text
    except ImportError:
        # Fallback giúp contract thuần Python vẫn chạy trước khi cài dependency đầy đủ.
        split_text = _split_text_fallback

    chunks = []
    for document in documents:
        validate_document(document)
        texts = split_text(document["content"])
        for index, text in enumerate(text for text in texts if text.strip()):
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text.strip(),
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
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
    get_collection().upsert(
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


def _split_text_fallback(text: str) -> list[str]:
    """Fallback theo ký tự, có overlap; không được dùng để tạo dữ liệu giả."""
    if len(text) <= CHUNK_SIZE:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            boundary = max(text.rfind(separator, start, end) for separator in ("\n\n", "\n", ". ", " "))
            if boundary > start + CHUNK_SIZE // 2:
                end = boundary + 1
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
