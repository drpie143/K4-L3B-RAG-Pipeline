"""Dữ liệu mẫu cho chế độ demo của giao diện.

Chỉ dùng khi backend (Task 10) chưa sẵn sàng. Nội dung các đoạn trích lấy từ
corpus thật trong data/standardized nhưng điểm số và câu trả lời là giả lập.
Mọi dict ở đây theo đúng schema trong docs/MODULE_CONTRACTS.md.
"""

URL_141 = "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-141-2026-nd-cp-469455.htm"
URL_168 = "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-168-2025-nd-cp-45354.htm"
URL_117 = "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-117-2025-nd-cp-45045/56698.htm"
URL_254 = "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-254-2026-nd-cp-469957.htm"
URL_A01 = "https://baochinhphu.vn/chinh-thuc-nang-nguong-chiu-thue-voi-ho-kinh-doanh-len-01-ty-dong-nam-ap-dung-tu-1-1-2026-102260429185517215.htm"
URL_A02 = "https://baochinhphu.vn/quy-dinh-moi-ve-dang-ky-ho-kinh-doanh-102250702150908133.htm"
URL_A05 = "https://baochinhphu.vn/quy-dinh-quan-ly-thue-doi-voi-ho-ca-nhan-kinh-doanh-tren-nen-tang-thuong-mai-dien-tu-102250611153921023.htm"


def _source(doc_id, chunk, title, source, doc_type, url, content, score, method):
    return {
        "id": f"{doc_id}::chunk-{chunk}",
        "content": content,
        "score": score,
        "metadata": {
            "source": source,
            "title": title,
            "doc_type": doc_type,
            "url": url,
            "chunk_index": chunk,
        },
        "retrieval_method": method,
    }


SRC_141_THRESHOLD = _source(
    "legal/nghi-dinh-141-2026-sua-doi-nghi-dinh-68-thue-ho-kinh-doanh", 3,
    "Nghị định 141/2026/NĐ-CP sửa đổi Nghị định 68/2026/NĐ-CP (nâng ngưỡng doanh thu không chịu thuế lên 01 tỷ đồng)",
    "nghi-dinh-141-2026-sua-doi-nghi-dinh-68-thue-ho-kinh-doanh.docx", "legal", URL_141,
    "Điều 1. 1. Sửa đổi cụm từ “500 triệu đồng” thành “01 tỷ đồng” tại Điều 3, Điều 4, khoản 1 Điều 8, "
    "Điều 9, Điều 10, khoản 3 Điều 11, khoản 1 và khoản 2 Điều 12, khoản 4 Điều 17, khoản 3 Điều 18 "
    "Nghị định số 68/2026/NĐ-CP.",
    0.0325, "hybrid",
)
SRC_141_INVOICE = _source(
    "legal/nghi-dinh-141-2026-sua-doi-nghi-dinh-68-thue-ho-kinh-doanh", 4,
    "Nghị định 141/2026/NĐ-CP sửa đổi Nghị định 68/2026/NĐ-CP (nâng ngưỡng doanh thu không chịu thuế lên 01 tỷ đồng)",
    "nghi-dinh-141-2026-sua-doi-nghi-dinh-68-thue-ho-kinh-doanh.docx", "legal", URL_141,
    "5. Sử dụng hóa đơn điện tử. a) Hộ kinh doanh, cá nhân kinh doanh có doanh thu năm trên 01 tỷ đồng thì "
    "phải áp dụng hóa đơn điện tử có mã của cơ quan thuế, hóa đơn điện tử khởi tạo từ máy tính tiền có kết "
    "nối dữ liệu với cơ quan thuế.",
    0.0318, "hybrid",
)
SRC_A01 = _source(
    "news/article_01", 1,
    "Chính thức: Nâng ngưỡng chịu thuế với hộ kinh doanh lên 01 tỷ đồng/năm, áp dụng từ 1/1/2026",
    "article_01.json", "news", URL_A01,
    "Chính phủ ban hành Nghị định số 141/2026/NĐ-CP ngày 29/4/2026 sửa đổi, bổ sung một số điều của Nghị định "
    "số 68/2026/NĐ-CP quy định về chính sách thuế đối với hộ kinh doanh, cá nhân kinh doanh. Nghị định này có "
    "hiệu lực thi hành từ ngày 01/01/2026.",
    0.0310, "hybrid",
)
SRC_254_POS = _source(
    "legal/nghi-dinh-254-2026-hoa-don-dien-tu", 41,
    "Nghị định 254/2026/NĐ-CP về hóa đơn điện tử, chứng từ điện tử",
    "nghi-dinh-254-2026-hoa-don-dien-tu.docx", "legal", URL_254,
    "Hóa đơn điện tử khởi tạo từ máy tính tiền có kết nối dữ liệu điện tử với cơ quan thuế là hóa đơn điện tử "
    "có mã của cơ quan thuế hoặc hóa đơn điện tử không có mã của cơ quan thuế hoặc dữ liệu điện tử để người "
    "mua có thể truy xuất, kê khai.",
    0.0294, "hybrid",
)
SRC_168_RIGHT = _source(
    "legal/nghi-dinh-168-2025-dang-ky-doanh-nghiep-phan-2", 0,
    "Nghị định 168/2025/NĐ-CP về đăng ký doanh nghiệp (phần 2: Chương VIII hộ kinh doanh trở đi)",
    "nghi-dinh-168-2025-dang-ky-doanh-nghiep-phan-2.pdf", "legal", URL_168,
    "Điều 82. Quyền thành lập hộ kinh doanh. 1. Hộ kinh doanh do một cá nhân hoặc các thành viên hộ gia đình "
    "đăng ký thành lập và chịu trách nhiệm bằng toàn bộ tài sản của mình đối với hoạt động kinh doanh của hộ.",
    0.0328, "hybrid",
)
SRC_168_EXCEPT = _source(
    "legal/nghi-dinh-168-2025-dang-ky-doanh-nghiep-phan-2", 1,
    "Nghị định 168/2025/NĐ-CP về đăng ký doanh nghiệp (phần 2: Chương VIII hộ kinh doanh trở đi)",
    "nghi-dinh-168-2025-dang-ky-doanh-nghiep-phan-2.pdf", "legal", URL_168,
    "2. Cá nhân, thành viên hộ gia đình là công dân Việt Nam có năng lực hành vi dân sự đầy đủ theo quy định "
    "của Bộ luật Dân sự có quyền thành lập hộ kinh doanh, trừ các trường hợp sau đây: a) Người đang bị truy "
    "cứu trách nhiệm hình sự, bị tạm giam, đang chấp hành hình phạt tù...; b) Người không được thành lập hộ "
    "kinh doanh theo quy định của luật.",
    0.0320, "hybrid",
)
SRC_A02 = _source(
    "news/article_02", 0,
    "Quy định mới về đăng ký hộ kinh doanh",
    "article_02.json", "news", URL_A02,
    "Tại Nghị định 168/2025/NĐ-CP về đăng ký doanh nghiệp, Chính phủ nêu rõ quy định về hộ kinh doanh và "
    "đăng ký hộ kinh doanh.",
    0.0288, "hybrid",
)
SRC_117 = _source(
    "legal/nghi-dinh-117-2025-thue-thuong-mai-dien-tu", 6,
    "Nghị định 117/2025/NĐ-CP về quản lý thuế đối với kinh doanh trên nền tảng thương mại điện tử, nền tảng số của hộ, cá nhân",
    "nghi-dinh-117-2025-thue-thuong-mai-dien-tu.pdf", "legal", URL_117,
    "Điều 4. Khấu trừ, nộp thuế thay. 1. Tổ chức quản lý nền tảng thương mại điện tử trong và ngoài nước "
    "thuộc đối tượng khấu trừ, nộp thuế thay thực hiện khấu trừ, nộp thuế thay số thuế giá trị gia tăng phải "
    "nộp đối với từng giao dịch của hộ, cá nhân kinh doanh.",
    0.71, "pageindex",
)
SRC_A05 = _source(
    "news/article_05", 3,
    "Quy định quản lý thuế đối với kinh doanh trên nền tảng thương mại điện tử",
    "article_05.json", "news", URL_A05,
    "Hộ, cá nhân kinh doanh đã được tổ chức quản lý nền tảng thương mại điện tử khấu trừ, nộp thuế thay thì "
    "không phải khai, nộp thuế giá trị gia tăng, thuế thu nhập cá nhân đối với các hoạt động kinh doanh trên "
    "nền tảng thương mại điện tử đã khấu trừ, nộp thuế thay.",
    0.64, "pageindex",
)

SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

# Câu hỏi gợi ý hiển thị ở màn hình trống; khóa khớp với MOCK_ANSWERS.
EXAMPLE_QUESTIONS = [
    "Hộ kinh doanh có doanh thu bao nhiêu thì không phải nộp thuế GTGT và TNCN?",
    "Ai có quyền thành lập hộ kinh doanh?",
    "Hộ kinh doanh nào bắt buộc dùng hóa đơn điện tử từ máy tính tiền?",
    "Sàn thương mại điện tử có khấu trừ thuế thay cho người bán không?",
    "Thủ tục xin visa du lịch Nhật Bản như thế nào?",
]

MOCK_ANSWERS = {
    EXAMPLE_QUESTIONS[0]: {
        "answer": (
            "Từ ngày **01/01/2026**, hộ kinh doanh, cá nhân kinh doanh có doanh thu năm **từ 01 tỷ đồng trở xuống** "
            "không phải nộp thuế giá trị gia tăng và thuế thu nhập cá nhân [S1]. Ngưỡng này được nâng từ mức "
            "500 triệu đồng quy định ban đầu tại Nghị định 68/2026/NĐ-CP [S1][S2].\n\n"
            "Nghị định 141/2026/NĐ-CP ban hành ngày 29/4/2026 nhưng có hiệu lực hồi tố từ 01/01/2026 [S3]."
        ),
        "sources": [SRC_141_THRESHOLD, SRC_141_INVOICE, SRC_A01],
        "retrieval_source": "hybrid",
    },
    EXAMPLE_QUESTIONS[1]: {
        "answer": (
            "Hộ kinh doanh do **một cá nhân** hoặc **các thành viên hộ gia đình** đăng ký thành lập, và chịu trách "
            "nhiệm bằng toàn bộ tài sản của mình đối với hoạt động kinh doanh của hộ [S1].\n\n"
            "Người thành lập phải là công dân Việt Nam có năng lực hành vi dân sự đầy đủ, trừ các trường hợp như "
            "đang bị truy cứu trách nhiệm hình sự, tạm giam, chấp hành hình phạt tù hoặc bị cấm theo luật [S2]."
        ),
        "sources": [SRC_168_RIGHT, SRC_168_EXCEPT, SRC_A02],
        "retrieval_source": "hybrid",
    },
    EXAMPLE_QUESTIONS[2]: {
        "answer": (
            "Hộ kinh doanh, cá nhân kinh doanh có **doanh thu năm trên 01 tỷ đồng** phải áp dụng hóa đơn điện tử có "
            "mã của cơ quan thuế hoặc hóa đơn điện tử khởi tạo từ máy tính tiền có kết nối dữ liệu với cơ quan "
            "thuế [S1]. Hóa đơn từ máy tính tiền cho phép người mua truy xuất và kê khai thông tin hóa đơn [S2]."
        ),
        "sources": [SRC_141_INVOICE, SRC_254_POS],
        "retrieval_source": "hybrid",
    },
    EXAMPLE_QUESTIONS[3]: {
        "answer": (
            "Có. Tổ chức quản lý nền tảng thương mại điện tử (kể cả nước ngoài) thuộc diện khấu trừ phải "
            "**khấu trừ, nộp thuế thay** thuế GTGT và TNCN cho hộ, cá nhân kinh doanh [S1]. Khi đã được sàn nộp "
            "thay, người bán không phải tự khai, nộp lại phần thuế đó [S2]."
        ),
        "sources": [SRC_117, SRC_A05],
        "retrieval_source": "pageindex",
    },
}

REFUSAL_RESULT = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}

# Từ khóa để demo phân biệt câu hỏi trong/ngoài chủ đề khi người dùng tự gõ câu hỏi.
IN_DOMAIN_KEYWORDS = (
    "hộ kinh doanh", "thuế", "hóa đơn", "hoá đơn", "đăng ký", "doanh thu", "thương mại điện tử",
    "máy tính tiền", "cá nhân kinh doanh", "khấu trừ", "nghị định", "gtgt", "tncn",
)


# ---------------------------------------------------------------- Evaluation mẫu
METRICS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]

MOCK_EVALUATION = {
    "is_sample": True,
    "run_info": {
        "evaluation_date": "—",
        "framework": "RAGAS 0.4.3",
        "evaluator_model": "—",
        "generator_model": "—",
        "embedding_model": "—",
        "corpus_version": "—",
        "golden_size": 15,
        "top_k": 5,
        "score_threshold": "—",
    },
    "configs": {
        "A": {
            "label": "Dense-only",
            "overall": {"faithfulness": 0.81, "answer_relevancy": 0.78, "context_recall": 0.66, "context_precision": 0.70},
            "avg_latency_ms": 2150,
        },
        "B": {
            "label": "Hybrid + RRF",
            "overall": {"faithfulness": 0.86, "answer_relevancy": 0.83, "context_recall": 0.79, "context_precision": 0.76},
            "avg_latency_ms": 2380,
        },
    },
    "per_question": [
        {"question": EXAMPLE_QUESTIONS[0], "config": "A", "faithfulness": 0.62, "answer_relevancy": 0.80,
         "context_recall": 0.40, "context_precision": 0.55, "failure_stage": "retrieval",
         "root_cause": "Dense lấy Nghị định 68 (ngưỡng cũ 500 triệu) thay vì Nghị định 141"},
        {"question": EXAMPLE_QUESTIONS[0], "config": "B", "faithfulness": 0.95, "answer_relevancy": 0.91,
         "context_recall": 1.00, "context_precision": 0.83, "failure_stage": "", "root_cause": ""},
        {"question": EXAMPLE_QUESTIONS[1], "config": "A", "faithfulness": 0.90, "answer_relevancy": 0.86,
         "context_recall": 0.75, "context_precision": 0.80, "failure_stage": "", "root_cause": ""},
        {"question": EXAMPLE_QUESTIONS[1], "config": "B", "faithfulness": 0.93, "answer_relevancy": 0.88,
         "context_recall": 1.00, "context_precision": 0.85, "failure_stage": "", "root_cause": ""},
        {"question": EXAMPLE_QUESTIONS[2], "config": "A", "faithfulness": 0.58, "answer_relevancy": 0.66,
         "context_recall": 0.50, "context_precision": 0.45, "failure_stage": "retrieval",
         "root_cause": "Cụm 'máy tính tiền' hiếm, dense bỏ sót; BM25 bắt được"},
        {"question": EXAMPLE_QUESTIONS[2], "config": "B", "faithfulness": 0.88, "answer_relevancy": 0.84,
         "context_recall": 0.90, "context_precision": 0.78, "failure_stage": "", "root_cause": ""},
        {"question": EXAMPLE_QUESTIONS[3], "config": "A", "faithfulness": 0.74, "answer_relevancy": 0.71,
         "context_recall": 0.60, "context_precision": 0.62, "failure_stage": "generation",
         "root_cause": "Trả lời thiếu ý không phải khai lại thuế đã được sàn nộp thay"},
        {"question": EXAMPLE_QUESTIONS[3], "config": "B", "faithfulness": 0.70, "answer_relevancy": 0.74,
         "context_recall": 0.70, "context_precision": 0.58, "failure_stage": "data",
         "root_cause": "Chunk 500 ký tự cắt đôi Điều 4, mất ngữ cảnh"},
    ],
}
