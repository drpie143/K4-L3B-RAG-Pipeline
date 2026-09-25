"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import math
import re
from collections import Counter


CORPUS: list[dict] = []
_BM25_INDEX = None
_BM25_CORPUS_ID: int | None = None


def _tokenize(text: str) -> list[str]:
    """Tokenize Unicode nhất quán cho cả corpus và query."""
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


class BM25Index:
    """BM25 tối giản với IDF dương, hoạt động cả với corpus nhỏ."""

    def __init__(self, documents: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.lengths = [len(document) for document in documents]
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.frequencies = [Counter(document) for document in documents]
        document_frequency = Counter()
        for document in documents:
            document_frequency.update(set(document))
        count = len(documents)
        self.idf = {
            token: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = []
        for frequencies, length in zip(self.frequencies, self.lengths):
            score = 0.0
            for token in query_tokens:
                frequency = frequencies.get(token, 0)
                if not frequency:
                    continue
                length_normalization = 1 - self.b
                if self.average_length:
                    length_normalization += self.b * length / self.average_length
                denominator = frequency + self.k1 * length_normalization
                score += self.idf.get(token, 0.0) * (
                    frequency * (self.k1 + 1) / denominator
                )
            scores.append(score)
        return scores


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    return BM25Index([_tokenize(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    global CORPUS, _BM25_INDEX, _BM25_CORPUS_ID
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    if not CORPUS:
        from .task4_chunking_indexing import chunk_documents, load_documents

        CORPUS = chunk_documents(load_documents())
    if not CORPUS:
        return []

    if _BM25_INDEX is None or _BM25_CORPUS_ID != id(CORPUS):
        _BM25_INDEX = build_bm25_index(CORPUS)
        _BM25_CORPUS_ID = id(CORPUS)
    scores = _BM25_INDEX.get_scores(_tokenize(query))
    ranked_indices = sorted(range(len(CORPUS)), key=lambda index: (-scores[index], index))
    results = []
    seen = set()
    for index in ranked_indices:
        item = CORPUS[index]
        if scores[index] <= 0 or item["id"] in seen:
            continue
        seen.add(item["id"])
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        if len(results) == top_k:
            break
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
