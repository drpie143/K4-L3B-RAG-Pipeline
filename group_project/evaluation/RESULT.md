# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 25/09/2026  |
| Framework and version              | Langchain & Ragas 0.4.3 |
| Evaluator model                    | openai/gpt-4o-mini |
| Generator model                    | gemini/gemini-2.5-flash |
| Embedding model                    | sentence-transformers/bge-m3 |
| Corpus version/commit              | v1.0 |
| Golden dataset size                | 15 Q&A pairs |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.3 (Cosine) |

## Configurations

- **Config A — dense-only:** Chỉ dùng ChromaDB semantic search.
- **Config B — hybrid + RRF:** Dùng ChromaDB + BM25Okapi, gộp bằng Reciprocal Rank Fusion (k=60).

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.850 |    0.890 |    +0.040 |
| Answer relevance  |    0.820 |    0.875 |    +0.055 |
| Context recall    |    0.750 |    0.860 |    +0.110 |
| Context precision |    0.810 |    0.880 |    +0.070 |
| **Average**       |    0.807 |    0.876 |    +0.069 |

## A/B comparison

- Cấu hình tốt hơn: Config B (hybrid + RRF)
- Evidence: Điểm Context recall và precision tăng mạnh (lần lượt +0.11 và +0.07), do BM25 giúp bắt được chính xác tên riêng và mã số điều luật mà embedding bị bỏ sót.
- Trade-off về latency/cost: Thời gian truy vấn tăng nhẹ (từ ~150ms lên ~300ms) do phải quét thêm index BM25 và tính lại rank array.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Câu hỏi về số nghị định cụ thể | A      |         0.00 |      0.50 |   0.00 |      0.00 | retrieval | Dense model bỏ qua keyword mã số, lấy nhầm nghị định khác. |
|   2 | Giải thích thuật ngữ chuyên ngành | B      |         0.50 |      0.60 |   0.50 |      0.40 | generation | LLM không đủ context để hiểu trọn vẹn ngữ cảnh của luật cũ. |
|   3 | Thông báo sự kiện tháng trước | B      |         0.00 |      0.00 |   0.00 |      0.00 | data | Bài báo chưa được crawl về DB. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Thu thập thêm dữ liệu crawl | Failures do thiếu bài báo / văn bản | Tránh hallucination | Chạy lại query trên data mới |
|        2 | Tinh chỉnh BM25 tokenizer | Từ khóa tiếng Việt chưa tách từ tốt | Tăng recall lexical | Chạy Ragas kiểm tra context recall |
|        3 | Dùng LLM prompt tốt hơn | LLM chưa tuân thủ strictly context | Tăng faithfulness | Đọc log generation từ LLM |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Đổi `top_k=10` | `top_k=5` | +0.02 recall, -0.05 precision | +200ms latency, +50% cost | Không đáng kể, giữ top_k=5 là tối ưu. |
