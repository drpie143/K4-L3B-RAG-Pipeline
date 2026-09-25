# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | Retrieval evaluator nội bộ; RAGAS 0.4.3 đã chuẩn bị nhưng chưa chạy |
| Evaluator model                    | `gpt-5-mini` — chưa chạy do API key bị vô hiệu hóa |
| Generator model                    | `gpt-5-mini` — chưa chạy do API key bị vô hiệu hóa |
| Embedding model                    | `BAAI/bge-m3` |
| Corpus version/commit              | `d61ae1608bc9f3fb4e6473520bde4540844850cf` |
| Golden dataset size                | 15 grounded cases |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.55; hiệu chỉnh bằng 15 in-domain + 5 out-of-domain queries |

## Configurations

- **Config A — dense-only:** BGE-M3 cosine search, lấy top 5.
- **Config B — hybrid + RRF:** BGE-M3 và BM25 lấy 10 ứng viên mỗi nhánh, RRF `k=60`, lấy top 5.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      | Chưa chạy | Chưa chạy | N/A |
| Answer relevance  | Chưa chạy | Chưa chạy | N/A |
| Context recall    | Chưa chạy | Chưa chạy | N/A |
| Context precision | Chưa chạy | Chưa chạy | N/A |
| **Average**       | Chưa chạy | Chưa chạy | N/A |

Không điền số giả cho bốn LLM-based metrics. Script
`group_project/evaluation/evaluate_rag.py` đã sẵn sàng; lần chạy ngày 2026-09-25
bị chặn vì OpenAI trả `401 token_invalidated`.

### Retrieval scores đã đo được

| Metric | Dense | Hybrid + RRF | Delta B−A |
|---|---:|---:|---:|
| Source Hit@5 | 1.000 | 1.000 | 0.000 |
| Source MRR@5 | 0.806 | 0.889 | +0.083 |
| Context token recall | 0.987 | 0.987 | 0.000 |
| Mean latency | 125 ms | 131 ms | +6 ms |

## A/B comparison

- Cấu hình tốt hơn ở retrieval: hybrid + RRF.
- Evidence: giữ nguyên Hit@5 100% nhưng tăng MRR@5 từ 0.806 lên 0.889 trên cùng 15 câu.
- Trade-off về latency/cost: tăng khoảng 6 ms/query trên máy đánh giá; BM25 chạy local nên không tăng API cost.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Ai chịu trách nhiệm khấu trừ thuế trên nền tảng có thanh toán? | Hybrid | Chưa chạy | Chưa chạy | 0.931 token proxy | Chưa chạy | retrieval | Context cần ghép Điều 1 và Điều 2 của cùng văn bản |
|   2 | Đăng ký hộ kinh doanh qua mạng dùng tài khoản nào? | Hybrid | Chưa chạy | Chưa chạy | 0.966 token proxy | Chưa chạy | retrieval | Evidence ngắn, một số từ trong expected context không lặp nguyên dạng |
|   3 | Tạm ngừng từ bao nhiêu ngày và tối đa bao lâu? | Hybrid | Chưa chạy | Chưa chạy | 0.971 token proxy | Chưa chạy | retrieval | Một điều dài được chia thành nhiều part |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Thay OpenAI API key hợp lệ và chạy `evaluate_rag.py` | Bốn LLM-based metrics chưa có số | Hoàn thành báo cáo generation | File `ragas_results.json` có đủ 30 case A/B |
|        2 | Giữ chunk theo Điều nhưng đánh giá thêm các section nhiều part | Ba case recall proxy thấp nhất thuộc section dài/đa điều | Tăng context recall/precision | So sánh retrieval trước/sau trên cùng golden set |
|        3 | Thêm test ưu tiên văn bản sửa đổi mới hơn bài báo cũ | Corpus có cả ngưỡng 500 triệu và 01 tỷ | Giảm câu trả lời lỗi thời | Query ngưỡng thuế phải cite Nghị định 141/2026 |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Markdown hierarchy chunking | Recursive 500/50 overlap | MRR chưa có baseline tương đương | Giảm chunk từ 1.284 xuống 526 | Giữ cấu trúc Chương/Mục/Điều, không overlap |
