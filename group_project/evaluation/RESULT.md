# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | Retrieval evaluator nội bộ; RAGAS 0.4.3 |
| Evaluator model                    | `gpt-4o-mini` |
| Generator model                    | `gpt-5-mini` (reasoning effort `low`) |
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
| Faithfulness      | 0.967 | 0.939 | -0.028 |
| Answer relevance  | 0.527 | 0.532 | +0.006 |
| Context recall    | 0.933 | 0.933 | 0.000 |
| Context precision | 1.000 | 0.977 | -0.023 |
| **Average**       | **0.857** | **0.845** | **-0.011** |

Kết quả được chạy thật trên 15 câu cho mỗi cấu hình (30 case), lưu đầy đủ tại
`group_project/evaluation/ragas_results.json`; không dùng mock data hoặc điểm giả.

### Retrieval scores đã đo được

| Metric | Dense | Hybrid + RRF | Delta B−A |
|---|---:|---:|---:|
| Source Hit@5 | 1.000 | 1.000 | 0.000 |
| Source MRR@5 | 0.806 | 0.889 | +0.083 |
| Context token recall | 0.987 | 0.987 | 0.000 |
| Mean latency | 125 ms | 131 ms | +6 ms |

## A/B comparison

- Hybrid + RRF tốt hơn ở thứ hạng retrieval: giữ Hit@5 100% và tăng MRR@5 từ
  0.806 lên 0.889 trên cùng 15 câu.
- Dense tốt hơn nhẹ ở trung bình RAGAS (0.857 so với 0.845), chủ yếu nhờ
  faithfulness và context precision. Hybrid chỉ tăng answer relevance 0.006.
- Trade-off của hybrid: tăng khoảng 6 ms/query trên máy đánh giá; BM25 chạy local
  nên không tăng API cost. Với corpus hiện tại, nên giữ hybrid cho khả năng xếp
  đúng nguồn nhưng tiếp tục lọc context trước generation.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Nghị định 141/2026 thay ngưỡng 500 triệu thành mức nào? | Dense/Hybrid | 0.500 | 0.559/0.559 | 1.000 | 1.000 | evaluation | Câu trả lời khớp reference nhưng trích hai nguồn tương đương; cần kiểm tra độ ổn định của LLM judge |
|   2 | Ủy quyền làm thủ tục có bắt buộc công chứng, chứng thực không? | Hybrid | 0.750 | 0.834 | 0.500 | 1.000 | retrieval + generation | Câu trả lời thêm diễn giải về văn bản sửa đổi ngoài ý chính của reference |
|   3 | Doanh thu trên 01 tỷ có bắt buộc dùng hóa đơn điện tử không? | Dense/Hybrid | 1.000 | 0.509/0.549 | 0.500 | 1.000 | retrieval + generation | Câu trả lời thêm thời hạn 30 ngày; evidence liên quan nằm ở nhiều văn bản |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Thêm bước lọc/rerank top-5 sau RRF theo văn bản và điều khoản | Hybrid context precision 0.977, thấp hơn dense 1.000 | Giữ lợi thế MRR nhưng giảm context nhiễu | Rerun cùng 30 case; precision ≥ dense và MRR không giảm |
|        2 | Bổ sung liên kết các chunk cùng Điều cho câu có quy tắc và ngoại lệ | Hai case context recall chỉ đạt 0.500 | Tăng recall mà không tăng `top_k` toàn cục | Hai case 5 và 12 đạt recall > 0.5 |
|        3 | Tránh citation trùng nghĩa và chạy LLM judge lặp để kiểm tra độ ổn định | Case 11 khớp reference nhưng faithfulness chỉ 0.500 ở cả hai config | Phân biệt lỗi generation với nhiễu evaluator | Chấm case 11 ba lần và báo median/độ lệch |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Markdown hierarchy chunking | Recursive 500/50 overlap | MRR chưa có baseline tương đương | Giảm chunk từ 1.284 xuống 526 | Giữ cấu trúc Chương/Mục/Điều, không overlap |
