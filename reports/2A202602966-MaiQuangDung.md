# Individual contribution report

## Thông tin

- Họ và tên: Mai Quang Dũng
- Mã học viên: 2A20260296
- Nhóm : The Liems
- Repository/branch: QuangDung
## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4, 5, 6, 7 | Implement logic chunking, semantic & lexical search, và RRF reranking | `src/task4...`, `src/task5...` | Done |
| Task 9, 10 | Hoàn thiện retrieval pipeline tổng hợp và generation LLM | `src/task9...`, `src/task10...` | Done |

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Sử dụng `SentenceTransformer("BAAI/bge-m3")` chạy cục bộ và cache singleton để nhúng.  
   **Lý do/evidence:** Tiết kiệm chi phí API và tăng tốc độ xử lý hàng loạt trên máy tính cá nhân.  
   **Trade-off:** Mất nhiều RAM hơn trên máy so với việc gọi API ngoài, lần load đầu tiên hơi chậm.

2. **Quyết định:** Dùng thuật toán BM25Okapi và công thức RRF `1 / (60 + rank)` để kết hợp kết quả.  
   **Lý do/evidence:** BM25 rất tốt cho tìm kiếm từ khóa chính xác, trong khi embedding tốt cho ngữ nghĩa.  
   **Trade-off:** Cần lưu trữ và xử lý cả index text thuần và vector (ChromaDB), pipeline tốn gấp đôi số truy vấn (semantic + lexical).

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest tests/test_contracts.py -q`
- Kết quả trước/sau nếu có: Passed 100% tất cả test cases.
- Lỗi đã phát hiện và cách xử lý: Quên cache `SentenceTransformer`, sửa bằng cách dùng `global _model`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Tốc độ BM25 tính trong Python thuần sẽ chậm nếu corpus lên đến hàng nghìn document.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Dùng Elasticsearch hoặc meilisearch thay vì tính BM25 thủ công bằng numpy trên memory.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Nguyễn Văn A
