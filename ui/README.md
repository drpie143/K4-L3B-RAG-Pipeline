# Giao diện Streamlit

```bash
streamlit run app.py
```

| File | Nội dung |
|---|---|
| `app.py` | Cấu hình trang, thanh điều hướng 3 trang, sidebar chung |
| `ui/page_chat.py` | Chatbot: câu hỏi mẫu, câu trả lời có citation `[S1]`, thẻ nguồn, safe refusal |
| `ui/page_evaluation.py` | Đánh giá A/B: 4 metric, biểu đồ, theo từng câu hỏi, golden dataset, tiến độ |
| `ui/page_corpus.py` | Kho tài liệu: thống kê, bảng tài liệu, xem nội dung theo mục lục |
| `ui/backend.py` | **Điểm nối backend duy nhất** — UI chỉ gọi các hàm ở đây |
| `ui/mock_data.py` | Dữ liệu demo khi backend chưa xong |

## Nối backend thật

Không cần sửa code UI. Chỉ cần:

1. **Chatbot** — `src.task10_generation.generate_with_citation(query, top_k)` trả `GenerationResult`
   đúng `docs/MODULE_CONTRACTS.md`. Hàm hết `NotImplementedError` là UI tự chuyển từ demo sang thật.
   - Muốn nút *Hybrid + RRF / Dense-only* có tác dụng: thêm tham số `use_reranking: bool = True`
     và truyền xuống `retrieve(..., use_reranking=...)`.
   - `sources` phải sort theo score giảm dần (contract), `[S1]` là phần tử đầu tiên của `sources`.
2. **Đánh giá** — ghi kết quả RAGAS vào `group_project/evaluation/eval_results.json`, cùng cấu trúc
   `MOCK_EVALUATION` trong `ui/mock_data.py` (bỏ khóa `is_sample`).
3. **Golden dataset** — `group_project/evaluation/golden_dataset.json`: list `{question, expected_answer, expected_context}`.

Biến môi trường `RAG_UI_MODE`: `auto` (mặc định), `demo` (luôn dùng dữ liệu mẫu), `real` (luôn gọi backend, lỗi sẽ hiện ra).
Bật **Hiện chẩn đoán** ở sidebar để xem JSON backend trả về và kiểm tra có đúng contract không.
