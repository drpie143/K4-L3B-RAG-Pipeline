"""Đánh giá retrieval thật trên golden dataset, không gọi LLM hay PageIndex."""

import json
import statistics
import subprocess
import time
from pathlib import Path

from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank_rrf


ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = Path(__file__).with_name("golden_dataset.json")
OUTPUT_PATH = Path(__file__).with_name("retrieval_results.json")
TOP_K = 5

OUT_OF_DOMAIN_QUERIES = [
    "Thời tiết Hà Nội ngày mai thế nào?",
    "Cách nấu phở bò ngon tại nhà",
    "Đội nào vô địch bóng đá thế giới gần nhất?",
    "Viết hàm Python sắp xếp một danh sách",
    "Triệu chứng cảm cúm nên uống thuốc gì?",
]


def _expected_source(item: dict) -> str:
    return item["source"].split(" — ", 1)[0].strip()


def _context_recall(expected: str, results: list[dict]) -> float:
    expected_tokens = set(expected.casefold().split())
    retrieved_tokens = set(" ".join(result["content"] for result in results).casefold().split())
    return len(expected_tokens & retrieved_tokens) / len(expected_tokens) if expected_tokens else 0.0


def _metrics(rows: list[dict], method: str) -> dict:
    reciprocal_ranks = []
    recalls = []
    for row in rows:
        result = row[method]
        reciprocal_ranks.append(1 / result["source_rank"] if result["source_rank"] else 0.0)
        recalls.append(result["context_token_recall"])
    return {
        "hit_at_5": sum(value > 0 for value in reciprocal_ranks) / len(rows),
        "mrr_at_5": statistics.mean(reciprocal_ranks),
        "mean_context_token_recall": statistics.mean(recalls),
        "mean_latency_ms": statistics.mean(row[method]["latency_ms"] for row in rows),
    }


def _run_search(query: str, method: str) -> tuple[list[dict], float]:
    started = time.perf_counter()
    dense = semantic_search(query, top_k=TOP_K * 2)
    if method == "dense":
        results = dense[:TOP_K]
    else:
        sparse = lexical_search(query, top_k=TOP_K * 2)
        results = rerank_rrf([dense, sparse], top_k=TOP_K)
    return results, (time.perf_counter() - started) * 1000


def _threshold_calibration(in_scores: list[float], out_scores: list[float]) -> dict:
    candidates = sorted(set(in_scores + out_scores))
    candidates = [0.0] + [(left + right) / 2 for left, right in zip(candidates, candidates[1:])] + [1.0]
    best = None
    for threshold in candidates:
        true_positive = sum(score >= threshold for score in in_scores)
        true_negative = sum(score < threshold for score in out_scores)
        accuracy = (true_positive + true_negative) / (len(in_scores) + len(out_scores))
        candidate = (accuracy, threshold)
        if best is None or candidate > best:
            best = candidate
    return {
        "suggested_threshold": best[1],
        "classification_accuracy": best[0],
        "in_domain_min": min(in_scores),
        "in_domain_median": statistics.median(in_scores),
        "out_of_domain_max": max(out_scores),
        "out_of_domain_median": statistics.median(out_scores),
    }


def main() -> None:
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    # Warm-up model và BM25 để latency không bao gồm thời gian nạp model lần đầu.
    semantic_search(golden[0]["question"], top_k=1)
    lexical_search(golden[0]["question"], top_k=1)
    rows = []
    in_scores = []
    for item in golden:
        expected_source = _expected_source(item)
        row = {"question": item["question"], "expected_source": expected_source}
        for method in ("dense", "hybrid"):
            results, latency = _run_search(item["question"], method)
            source_rank = next(
                (index for index, result in enumerate(results, 1)
                 if result["metadata"]["source"] == expected_source),
                None,
            )
            row[method] = {
                "source_rank": source_rank,
                "context_token_recall": _context_recall(item["expected_context"], results),
                "latency_ms": latency,
                "result_ids": [result["id"] for result in results],
            }
            if method == "dense":
                in_scores.append(results[0]["score"] if results else 0.0)
        rows.append(row)

    out_scores = []
    for query in OUT_OF_DOMAIN_QUERIES:
        results = semantic_search(query, top_k=1)
        out_scores.append(results[0]["score"] if results else 0.0)

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"

    output = {
        "corpus_commit": commit,
        "top_k": TOP_K,
        "golden_size": len(golden),
        "dense": _metrics(rows, "dense"),
        "hybrid": _metrics(rows, "hybrid"),
        "threshold_calibration": _threshold_calibration(in_scores, out_scores),
        "out_of_domain": [
            {"question": query, "best_dense_score": score}
            for query, score in zip(OUT_OF_DOMAIN_QUERIES, out_scores)
        ],
        "cases": rows,
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: output[key] for key in ("dense", "hybrid", "threshold_calibration")}, indent=2))
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
