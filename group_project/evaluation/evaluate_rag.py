"""Chạy A/B generation và bốn RAGAS metrics khi API key hợp lệ."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.task10_generation import generate_from_chunks
from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank_rrf


load_dotenv()

GOLDEN_PATH = Path(__file__).with_name("golden_dataset.json")
OUTPUT_PATH = Path(__file__).with_name("ragas_results.json")
GENERATION_CACHE_PATH = Path(__file__).with_name("rag_generation_cache.json")
TOP_K = 5


def _retrieve(question: str, hybrid: bool) -> list[dict]:
    dense = semantic_search(question, top_k=TOP_K * 2)
    if not hybrid:
        return dense[:TOP_K]
    sparse = lexical_search(question, top_k=TOP_K * 2)
    return rerank_rrf([dense, sparse], top_k=TOP_K)


def _build_rows(golden: list[dict], hybrid: bool) -> list[dict]:
    rows = []
    for index, item in enumerate(golden, 1):
        chunks = _retrieve(item["question"], hybrid=hybrid)
        generated = None
        for attempt in range(3):
            generated = generate_from_chunks(item["question"], chunks)
            if generated["retrieval_source"] != "none":
                break
            print(f"Retrying generation for case {index} ({attempt + 1}/3)")
        assert generated is not None
        if generated["retrieval_source"] == "none":
            raise RuntimeError(
                f"Generation failed for case {index}; verify LLM_MODEL and API key"
            )
        rows.append({
            "user_input": item["question"],
            "response": generated["answer"],
            "retrieved_contexts": [chunk["content"] for chunk in generated["sources"]],
            "reference": item["expected_answer"],
        })
        print(f"Generated {index}/{len(golden)} ({'hybrid' if hybrid else 'dense'})")
    return rows


def _evaluate(rows: list[dict]) -> tuple[dict, list[dict]]:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    model = os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini")
    evaluator = LangchainLLMWrapper(
        ChatOpenAI(model=model, timeout=60, max_retries=2)
    )
    embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model="text-embedding-3-small", max_retries=2)
    )
    result = evaluate(
        dataset=EvaluationDataset.from_list(rows),
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=evaluator,
        embeddings=embeddings,
        raise_exceptions=True,
    )
    frame = result.to_pandas()
    metric_names = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    aggregate = {
        metric: float(frame[metric].mean())
        for metric in metric_names
    }
    return aggregate, json.loads(frame.to_json(orient="records", force_ascii=False))


def main() -> None:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY is not configured")
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    cache = (
        json.loads(GENERATION_CACHE_PATH.read_text(encoding="utf-8"))
        if GENERATION_CACHE_PATH.is_file()
        else {}
    )
    output = {"top_k": TOP_K, "golden_size": len(golden), "configs": {}}
    for name, hybrid in (("dense", False), ("hybrid_rrf", True)):
        rows = cache.get(name)
        expected_questions = [item["question"] for item in golden]
        if not isinstance(rows, list) or [row.get("user_input") for row in rows] != expected_questions:
            rows = _build_rows(golden, hybrid=hybrid)
            cache[name] = rows
            GENERATION_CACHE_PATH.write_text(
                json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            print(f"Loaded {len(rows)} cached generations ({name})")
        aggregate, cases = _evaluate(rows)
        output["configs"][name] = {"aggregate": aggregate, "cases": cases}
        OUTPUT_PATH.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(name, aggregate)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
