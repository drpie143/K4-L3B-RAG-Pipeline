# Individual contribution report

## Thông tin

- Họ và tên: Đặng Đỉnh Đoàn
- Mã học viên: 2A202602927
- Nhóm: THE LIEMS
- Repository/branch: `drpie143/K4-L3B-RAG-Pipeline` / `Doan` (Task 1–3 đã merge vào `main` qua `da14569`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập văn bản pháp luật (Task 1) | Chọn 6 nghị định (7 file) về đăng ký, thuế, hóa đơn, TMĐT của hộ kinh doanh; tải từ Công báo điện tử, ghi số hiệu, ngày ban hành và ngày hiệu lực | `src/task1_collect_legal_docs.py`, `data/landing/legal/` — `0dbc29f` | Done |
| Thu thập bài viết (Task 2) | Crawl 7 bài (Báo Chính phủ, xaydungchinhsach.chinhphu.vn, VnExpress) bằng `requests` + BeautifulSoup, lưu JSON đủ `url`, `title`, `date_crawled`, `content_markdown` | `src/task2_crawl_news.py`, `data/landing/news/` — `0dbc29f` | Done |
| Chuẩn hóa Markdown (Task 3) | Convert PDF/DOCX bằng MarkItDown, làm sạch, chuẩn hóa tiêu đề `## Chương`/`### Điều`, thêm front matter metadata | `src/task3_convert_markdown.py`, `data/standardized/` (14 file) — `0dbc29f` | Done |
| Giao diện Streamlit | Thiết kế UI 3 trang (Chatbot, Đánh giá A/B, Kho tài liệu), citation `[S#]`, thẻ nguồn, safe refusal, adapter `ui/backend.py` để nối backend | `app.py`, `ui/`, `.streamlit/config.toml` — `9ff9166` (nhánh `Doan`) | Partial — chưa merge vào `main`, chưa nối backend thật |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Đổi nguồn văn bản từ PDF của vanban.chinhphu.vn sang file DOCX/PDF của Công báo điện tử.  
   **Lý do/evidence:** 5 PDF đầu tiên là bản scan: `pdfplumber` cho `0` ký tự text/trang, MarkItDown trả `0` ký tự. File Công báo có lớp text; sau khi chuyển, số thứ tự Điều liên tục trong mọi văn bản (168: Điều 1–81 và 82–124; 254: 1–45; 68: 1–19; 296: 1–22; 117: 1–13; 141: 1–5).  
   **Trade-off:** Văn bản 2025 trên Công báo chỉ có `.doc` (Word 97) nên phải dùng PDF, nối dòng bằng heuristic nên kém sạch hơn DOCX. Link tải có token nên code phải lấy lại từ trang văn bản mỗi lần chạy.

2. **Quyết định:** Chuẩn hóa cấu trúc pháp lý (`## Chương`, `### Điều`) và ghi `number`, `issued`, `effective` vào front matter thay vì chỉ dump text từ MarkItDown.  
   **Lý do/evidence:** Giúp chunk và trích dẫn theo Điều; metadata ngày hiệu lực cho phép ưu tiên văn bản mới, cần thiết vì Nghị định 141/2026 sửa ngưỡng miễn thuế từ 500 triệu lên 1 tỷ đồng còn Nghị định 68/2026 và hai bài báo vẫn ghi mức cũ.  
   **Trade-off:** Regex phụ thuộc định dạng Công báo. Phụ lục mẫu tờ khai của Nghị định 117 bị bỏ vì PDF trích thành bảng lộn xộn.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest tests/test_acceptance.py` (test dữ liệu legal, news, standardized); tải lại Task 1, crawl lại Task 2 và chạy lại Task 3 vào thư mục tạm để so sánh; chạy UI bằng Streamlit và chụp ảnh 3 trang ở chế độ sáng/tối.
- Kết quả trước/sau nếu có: Task 1 giống hệt từng byte (7/7 file), Task 2 giống hệt nội dung (7/7 bài, bỏ `date_crawled`), Task 3 chạy 2 lần cho cùng output. Toàn bộ `pytest -q` trên `main` hiện là 20 passed.
- Lỗi đã phát hiện và cách xử lý: PDF scan (đổi nguồn, xem quyết định 1); DOCX Công báo dùng `\` trong đường dẫn zip nên MarkItDown báo lỗi (đóng gói lại trước khi convert); tên chương bị ngắt dòng và Chương IV của Nghị định 168 mất tên (sửa trong Task 3); `date_crawled` thiếu múi giờ; `beautifulsoup4`/`lxml` chưa khai báo trong `pyproject.toml`; một bài trùng ~16/25 đoạn với bài khác (thay bằng bài về đăng ký hộ kinh doanh).

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: chưa xác nhận Nghị định 117/2025 còn hiệu lực sau 01/07/2026 khi Luật Quản lý thuế 108/2025 có hiệu lực (không tìm thấy văn bản thay thế). Hai PDF Công báo năm 2025 chưa được đối chiếu toàn bộ với bản gốc. UI chưa được thử với backend thật, và trang Đánh giá đọc `eval_results.json` với cấu trúc riêng, khác `ragas_results.json` hiện có.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: merge UI vào `main`, viết bộ chuyển đổi từ `ragas_results.json` sang định dạng UI, rồi demo đủ 3 trường hợp (câu hỏi đúng, ngoài phạm vi, so sánh A/B).

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Đặng Đỉnh Đoàn
