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
- `TEAMMATES.md` ghi thành viên, nhánh và commit phụ trách.
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

Điền API key cần dùng trong `.env`; không commit file này. Cấu hình tối thiểu để
chạy đầy đủ Task 8, Task 10 và evaluation:

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=gpt-5-mini
OPENAI_API_KEY=...
OPENAI_REASONING_EFFORT=low
RAGAS_LLM_MODEL=gpt-4o-mini
PAGEINDEX_API_KEY=...
SCORE_THRESHOLD=0.55
```

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Chunk, index và thử từng retrieval component
python -m src.task4_chunking_indexing
python -m src.task5_semantic_search
python -m src.task6_lexical_search
python -m src.task7_reranking

# 3. Upload PageIndex, chạy retrieval và generation
# Lần đầu Task 8 sẽ tạo/upload PDF và có thể mất vài phút.
python -m src.task8_pageindex_vectorless
python -m src.task9_retrieval_pipeline
python -m src.task10_generation

# 4. Tái tạo kết quả evaluation
python -m group_project.evaluation.evaluate_retrieval
# Gọi OpenAI nhiều lần và có phát sinh API cost.
python -m group_project.evaluation.evaluate_rag

# 5. Chạy toàn bộ test
pytest -q

# 6. Chạy sản phẩm
streamlit run app.py
```

Các artifact cần kiểm tra sau khi chạy:

- `chroma_db/`: vector store local, không commit.
- `pageindex_doc_ids.json`, `pageindex_pdfs/`: cache Task 8, không commit.
- `group_project/evaluation/retrieval_results.json`: retrieval A/B và threshold.
- `group_project/evaluation/ragas_results.json`: 15 câu × 2 cấu hình và 4 metrics.
- `group_project/evaluation/RESULT.md`: bảng tổng hợp và failure analysis.

`evaluate_rag.py` lưu generation tạm vào file cache bị gitignore. Nếu evaluator
gặp lỗi, lần chạy sau tái sử dụng các câu đã sinh thay vì gọi lại toàn bộ.

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

## Kịch bản demo không phụ thuộc UI

Trước buổi demo, chạy `pytest -q`, sau đó kiểm tra ba tình huống:

1. **In-domain:** “Hộ kinh doanh tạm ngừng từ bao nhiêu ngày thì phải đăng ký và
   phải báo trước bao lâu?” Kết quả phải nêu 15 ngày, 03 ngày làm việc và có
   citation `[S#]`.
2. **Out-of-domain:** “Thời tiết Hà Nội ngày mai thế nào?” Kết quả phải từ chối
   an toàn, không tự tạo thông tin thời tiết hoặc citation giả.
3. **A/B:** trình bày `retrieval_results.json` và `ragas_results.json`. Hybrid giữ
   Hit@5 = 1,000 và tăng MRR@5 từ 0,806 lên 0,889; dense có RAGAS average 0,857
   so với hybrid 0,845 do context của hybrid nhiễu hơn nhẹ.

Để ép kiểm tra PageIndex fallback mà không sửa `.env`, có thể gọi:

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv/Scripts/python.exe -c "from src.task9_retrieval_pipeline import retrieve; print(retrieve('Hộ kinh doanh tạm ngừng từ bao nhiêu ngày?', top_k=3, score_threshold=1.1))"
```

PageIndex hiện tìm trên 14 tài liệu theo tuần tự nên lượt fallback thật có thể
mất vài phút; document ID đã được cache nên không upload lại nếu tài liệu không đổi.

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
