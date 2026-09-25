# Individual contribution report

## Thông tin

- Họ và tên: Ngô Anh Khoa
- Mã học viên: 2A202602965
- Nhóm: THE LIEMS
- Repository/branch: `drpie143/K4-L3B-RAG-Pipeline` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Chunking/indexing | Chunk hierarchy theo Chương/Mục/Điều không overlap, giữ metadata pháp lý, embedding BGE-M3 và Chroma upsert | `src/task4_chunking_indexing.py` | Done — 526 chunks đã index |
| Dense retrieval | Map Chroma cosine distance sang `SearchResult`, chuẩn hóa metadata và thứ tự | `src/task5_semantic_search.py` | Done |
| BM25 retrieval | Tokenize Unicode, BM25, lazy-load cùng corpus chunks với dense retrieval | `src/task6_lexical_search.py` | Done |
| Hybrid retrieval | Cài đặt RRF theo ID, chống trùng và không mutate input | `src/task7_reranking.py` | Done |
| Retrieval pipeline | Ghép dense + BM25, RRF một lần, fallback theo dense score, chịu lỗi provider | `src/task9_retrieval_pipeline.py` | Done |
| Generation/citation | Reorder context, metadata hiệu lực, nhãn `[S#]`, OpenAI Responses API và kiểm tra citation | `src/task10_generation.py` | Partial — API key hiện trả `token_invalidated` |
| Streamlit UI | Nối pipeline thật, lưu chat history, hiển thị nguồn/method/score | `app.py` | Partial — chờ corpus để demo end-to-end |
| Contract validation | Siết schema document/search/generation và `doc_type` | `src/contracts.py` | Done |

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng RRF để hợp nhất dense và BM25, không cộng trực tiếp hai loại score.  
   **Lý do/evidence:** Cosine similarity và BM25 có thang đo khác nhau; contract test xác nhận công thức rank bắt đầu từ 1 và kết quả không trùng ID.  
   **Trade-off:** RRF ổn định và dễ giải thích nhưng không tận dụng độ lớn score gốc trong bước fusion.

2. **Quyết định:** Dùng dense cosine score gốc để kích hoạt fallback và cô lập lỗi PageIndex.  
   **Lý do/evidence:** RRF score chỉ phản ánh thứ hạng; ba contract test kiểm tra fallback, fuse đúng một lần và provider error.  
   **Trade-off:** Threshold phải hiệu chỉnh lại sau khi có corpus và embedding model thật.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m pytest tests/test_contracts.py -q`; `python -m group_project.evaluation.evaluate_retrieval`.
- Kết quả trước/sau nếu có: contract tests 15/15 pass; chunk count giảm từ 1.284 xuống 526; hybrid MRR@5 đạt 0,889 so với dense 0,806 trên 15 câu thật.
- Lỗi đã phát hiện và cách xử lý: RRF/dense/BM25/retrieval/generation còn `NotImplementedError`; đã cài đặt theo module contract. Citation source được trả cùng thứ tự reorder để `[S#]` đối chiếu đúng.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: chưa đo generation/RAGAS và citation end-to-end vì OpenAI key hiện bị vô hiệu hóa; PageIndex chưa có API key.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: chạy generation/RAGAS bằng key hợp lệ và phân tích các câu retrieval/generation kém nhất.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Ngô Anh Khoa
