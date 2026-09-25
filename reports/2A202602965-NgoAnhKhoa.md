# Individual contribution report

## Thông tin

- Họ và tên: Ngô Anh Khoa
- Mã học viên: 2A202602965
- Nhóm: THE LIEMS
- Repository/branch: `drpie143/K4-L3B-RAG-Pipeline` / `main` (nhánh phát triển: `Khoa`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Chunking/indexing | Chunk hierarchy theo Chương/Mục/Điều không overlap, giữ metadata pháp lý, embedding BGE-M3 và Chroma upsert | `src/task4_chunking_indexing.py`; `0c0f0a7`, `776511b` | Done — 526 chunks đã index |
| Dense, BM25 và RRF | Chuẩn hóa `SearchResult`, BM25 cùng corpus, RRF theo ID và không mutate input | `src/task5_semantic_search.py`–`src/task7_reranking.py`; `0c0f0a7` | Done |
| Retrieval pipeline | Ghép dense + BM25, RRF một lần, threshold theo dense cosine score và fallback chịu lỗi provider | `src/task9_retrieval_pipeline.py`; `0c0f0a7`, `776511b` | Done |
| Generation/citation | Context có metadata pháp lý, nhãn `[S#]`, OpenAI Responses API, kiểm tra citation và safe refusal | `src/task10_generation.py`; `776511b`, `a4de4e4` | Done — đã gọi OpenAI thật |
| PageIndex validation | Phát hiện/sửa PDF trắng sau trang đầu, parse payload lồng nhau và retry polling | `src/task8_pageindex_vectorless.py`; `a4de4e4` | Done — 14 tài liệu đã index thật |
| Evaluation | Golden set 15 câu, hiệu chỉnh threshold, retrieval A/B và 4 RAGAS metrics cho 30 case | `group_project/evaluation/`; `776511b`, `a4de4e4` | Done |
| Contract validation | Siết schema document/search/generation, metadata và các invariant retrieval | `src/contracts.py`, `tests/` | Done — 20 tests pass |

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng RRF để hợp nhất dense và BM25, không cộng trực tiếp hai loại score.  
   **Lý do/evidence:** Cosine similarity và BM25 có thang đo khác nhau; contract test xác nhận công thức rank bắt đầu từ 1 và kết quả không trùng ID.  
   **Trade-off:** RRF ổn định và dễ giải thích nhưng không tận dụng độ lớn score gốc trong bước fusion.

2. **Quyết định:** Dùng dense cosine score gốc để kích hoạt fallback và cô lập lỗi PageIndex.  
   **Lý do/evidence:** RRF score chỉ phản ánh thứ hạng; threshold `0,55` được hiệu chỉnh bằng 15 câu in-domain và 5 câu out-of-domain.
   **Trade-off:** PageIndex Cloud chính xác theo cấu trúc tài liệu nhưng lần truy vấn đầu chậm và phụ thuộc dịch vụ ngoài.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest -q`; `python -m group_project.evaluation.evaluate_retrieval`; `python -m group_project.evaluation.evaluate_rag`; truy vấn fallback PageIndex thật.
- Kết quả trước/sau nếu có: 20/20 tests pass; chunk count giảm từ 1.284 xuống 526; hybrid MRR@5 đạt 0,889 so với dense 0,806; RAGAS hoàn tất 30 case với dense average 0,857 và hybrid average 0,845.
- Lỗi đã phát hiện và cách xử lý: PDF trung gian PageIndex chỉ có tiêu đề vì con trỏ `multi_cell` sai; đã reset về lề trái mỗi dòng và buộc re-index bằng renderer version. Payload `relevant_contents` lồng list đã được parse đệ quy; polling GET có retry/backoff. GPT-5 mini đôi lúc dùng hết output budget cho reasoning; đã đặt effort `low` và tăng output budget.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: hybrid cải thiện MRR nhưng context precision và faithfulness thấp hơn dense nhẹ; PageIndex fallback tìm tuần tự trên 14 tài liệu nên có độ trễ cao.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: thêm bước lọc/rerank context sau RRF và chạy lại cùng 30 case để kiểm chứng thay vì chỉ tăng độ phức tạp theo cảm tính.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Ngô Anh Khoa
