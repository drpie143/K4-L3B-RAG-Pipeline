# RAG Pipeline — Pháp luật cho hộ kinh doanh

## Mục tiêu

Chatbot RAG trả lời câu hỏi về đăng ký, thuế, hóa đơn điện tử và thương mại
điện tử dành cho hộ kinh doanh Việt Nam. Pipeline dùng hybrid retrieval,
citation và ưu tiên văn bản pháp luật mới hơn khi nguồn có thay đổi theo thời gian.

Corpus hiện có 7 văn bản pháp luật từ Công báo điện tử và 7 bài hướng dẫn/bài
báo công khai. Dữ liệu gốc nằm trong `data/landing/`; bản Markdown kèm metadata
nguồn, ngày ban hành và ngày hiệu lực nằm trong `data/standardized/`.

## Sản phẩm phải nộp

- Repository nhóm chạy được.
- 7 tài liệu pháp luật và 7 bài viết do nhóm tự thu thập.
- Pipeline: convert → chunk → index → dense + BM25 → RRF → fallback → generation có citation.
- Chatbot Streamlit hiển thị câu trả lời và nguồn đã dùng.
- Golden dataset tối thiểu 15 câu; đánh giá 4 metric và so sánh A/B.
- `group_project/evaluation/RESULT.md`.
- Mỗi thành viên nộp báo cáo cá nhân trong `reports/`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

Trên PowerShell dùng:

```powershell
Copy-Item .env.example .env
```

Điền API key cần dùng trong `.env`; không commit file này.

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index và kiểm tra contract
python -m src.task4_chunking_indexing
pytest -q

# 3. Chạy sản phẩm
streamlit run app.py
```

## Thiết kế retrieval hiện tại

- Chunk theo hierarchy Markdown `văn bản → chương → mục → điều → đoạn`, không
  dùng sliding-window overlap. Section dài mới được chia tiếp theo đoạn/câu.
- Embedding mặc định: `BAAI/bge-m3`; ChromaDB dùng cosine distance.
- BM25 và dense retrieval dùng chung 526 chunks; RRF hợp nhất theo ID đúng một lần.
- Threshold fallback được hiệu chỉnh ở `0.55` từ 15 câu in-domain và 5 câu
  out-of-domain. Kết quả chi tiết ở
  `group_project/evaluation/retrieval_results.json`.
- OpenAI generation dùng Responses API và model `gpt-5-mini`; câu trả lời phải
  có citation `[S#]`, nếu evidence không đủ hoặc provider lỗi sẽ từ chối an toàn.

Kết quả retrieval hiện tại (`top_k=5`):

| Cấu hình | Hit@5 | MRR@5 | Context token recall | Latency trung bình |
|---|---:|---:|---:|---:|
| Dense | 1.000 | 0.806 | 0.987 | 125 ms |
| Hybrid + RRF | 1.000 | 0.889 | 0.987 | 131 ms |

Kết quả generation/RAGAS thật trên 15 câu × 2 cấu hình:

| Cấu hình | Faithfulness | Answer relevance | Context recall | Context precision |
|---|---:|---:|---:|---:|
| Dense | 0.967 | 0.527 | 0.933 | 1.000 |
| Hybrid + RRF | 0.939 | 0.532 | 0.933 | 0.977 |

Chi tiết 30 case nằm trong `group_project/evaluation/ragas_results.json`. Task 8
đã được kiểm tra bằng PageIndex Cloud thật trên 14 tài liệu; cache document ID và
retry polling giúp tránh upload lại hoặc làm hỏng pipeline khi mạng chập chờn.

## Lộ trình 3 giờ

| Mốc                  | Thời gian | Kết quả cần có                           |
| -------------------- | --------: | ---------------------------------------- |
| 0. Setup             |   10 phút | Môi trường và `.env` sẵn sàng            |
| 1. Data              |   25 phút | ≥3 legal, ≥5 news, Markdown đã chuẩn hoá |
| 2. Index & search    |   30 phút | ChromaDB, dense search và BM25 chạy được |
| 3. Fusion & fallback |   25 phút | RRF và fallback tuân thủ contract        |
| 4. Generation & UI   |   30 phút | Chatbot trả lời có citation              |
| 5. Evaluation        |   30 phút | 15+ Q&A, 4 metric, A/B comparison        |
| 6. Demo & handoff    |   30 phút | Test, report, demo và push repository    |

## Lưu ý quy tắc để có code quality tốt:

- Dense và BM25 nên cùng trả về `SearchResult` theo một schema.
- RRF chỉ nên dùng để gộp thứ hạng và chỉ chạy một lần.
- Fallback dùng cosine score gốc của dense retrieval.
- Threshold phải được hiệu chỉnh trên query in domain và out of domain, không có một con số đúng cho mọi corpus.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md): schema, interface và invariant mà code/test nên tuân theo.
- [Step-by-step guide](docs/STEP_BY_STEP.md): thứ tự triển khai và tiêu chí hoàn thành từng bước.
- [Grading rubric](docs/GRADING_RUBRIC.md): Rubric thang điểm.
- [Individual report](group_project/ịndividual/INDIVIDUAL_REPORT.md): template báo cáo cá nhân.
- [Suggested topics](docs/SUGGESTED_TOPICS.md): danh sách chủ đề tham khảo, không bắt buộc.

## Kiểm tra

```bash
# Contract tests
pytest tests/test_contracts.py -q

# Acceptance tests
pytest tests/test_acceptance.py -q

# Toàn bộ
pytest -q
```
