"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.

Chủ đề của nhóm: pháp luật cho hộ kinh doanh (mốc dữ liệu: tháng 9/2026).

Nguồn: Công báo điện tử (congbao.chinhphu.vn). Không dùng bản PDF ký số trên
vanban.chinhphu.vn vì đó là bản scan (mỗi trang là một ảnh, không có text).
Ưu tiên DOCX (văn bản 2026). Văn bản 2025 trên Công báo chỉ có .doc (Word 97)
nên dùng bản PDF có lớp text. Link tải có token nên được lấy lại từ trang văn
bản mỗi lần chạy.
"""

import html
import re
import ssl
import tempfile
from pathlib import Path
from urllib.parse import unquote


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

HEADERS = {"User-Agent": "Mozilla/5.0 (K4-RAG-Lab; educational crawler)"}

# CDN của Công báo không gửi kèm chứng chỉ trung gian, nên phải tự bổ sung
# chứng chỉ trung gian chính thức của GlobalSign để vẫn giữ việc kiểm tra SSL.
GLOBALSIGN_INTERMEDIATE_URL = "http://secure.globalsign.com/cacert/gsrsaovsslca2018.crt"

FILE_SIGNATURES = {".pdf": b"%PDF", ".docx": b"PK"}

# file_hint: chuỗi có trong tên file tải về, dùng khi văn bản đăng ở nhiều số Công báo.
LEGAL_DOCUMENTS = [
    {
        "filename": "nghi-dinh-168-2025-dang-ky-doanh-nghiep-phan-1.pdf",
        "number": "168/2025/NĐ-CP",
        "title": "Nghị định 168/2025/NĐ-CP về đăng ký doanh nghiệp (phần 1: Chương I–VII)",
        "issued": "2025-06-30",
        "effective": "2025-07-01",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-168-2025-nd-cp-45354.htm",
        "file_hint": "885",
    },
    {
        "filename": "nghi-dinh-168-2025-dang-ky-doanh-nghiep-phan-2.pdf",
        "number": "168/2025/NĐ-CP",
        "title": "Nghị định 168/2025/NĐ-CP về đăng ký doanh nghiệp (phần 2: Chương VIII hộ kinh doanh trở đi)",
        "issued": "2025-06-30",
        "effective": "2025-07-01",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-168-2025-nd-cp-45354.htm",
        "file_hint": "887",
    },
    {
        "filename": "nghi-dinh-296-2026-sua-doi-nghi-dinh-168-dang-ky-doanh-nghiep.docx",
        "number": "296/2026/NĐ-CP",
        "title": "Nghị định 296/2026/NĐ-CP sửa đổi, bổ sung Nghị định 168/2025/NĐ-CP về đăng ký doanh nghiệp",
        "issued": "2026-07-23",
        "effective": "2026-07-23",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-296-2026-nd-cp-470177/67429.htm",
    },
    {
        "filename": "nghi-dinh-68-2026-thue-ho-kinh-doanh.docx",
        "number": "68/2026/NĐ-CP",
        "title": "Nghị định 68/2026/NĐ-CP về chính sách thuế và quản lý thuế đối với hộ kinh doanh, cá nhân kinh doanh",
        "issued": "2026-03-05",
        "effective": "2026-03-05",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-68-2026-nd-cp-469047.htm",
    },
    {
        "filename": "nghi-dinh-141-2026-sua-doi-nghi-dinh-68-thue-ho-kinh-doanh.docx",
        "number": "141/2026/NĐ-CP",
        "title": "Nghị định 141/2026/NĐ-CP sửa đổi Nghị định 68/2026/NĐ-CP (nâng ngưỡng doanh thu không chịu thuế lên 01 tỷ đồng)",
        "issued": "2026-04-29",
        "effective": "2026-01-01",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-141-2026-nd-cp-469455.htm",
    },
    {
        "filename": "nghi-dinh-254-2026-hoa-don-dien-tu.docx",
        "number": "254/2026/NĐ-CP",
        "title": "Nghị định 254/2026/NĐ-CP về hóa đơn điện tử, chứng từ điện tử",
        "issued": "2026-06-30",
        "effective": "2026-07-01",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-254-2026-nd-cp-469957.htm",
    },
    {
        "filename": "nghi-dinh-117-2025-thue-thuong-mai-dien-tu.pdf",
        "number": "117/2025/NĐ-CP",
        "title": "Nghị định 117/2025/NĐ-CP về quản lý thuế đối với kinh doanh trên nền tảng thương mại điện tử, nền tảng số của hộ, cá nhân",
        "issued": "2025-06-09",
        "effective": "2025-07-01",
        "page_url": "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-117-2025-nd-cp-45045/56698.htm",
    },
]


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def _build_ca_bundle(session) -> str:
    """Ghép bundle certifi với chứng chỉ trung gian GlobalSign; trả về đường dẫn file."""
    import certifi

    der = session.get(GLOBALSIGN_INTERMEDIATE_URL, timeout=30).content
    bundle = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
    bundle.write(Path(certifi.where()).read_text())
    bundle.write("\n" + ssl.DER_cert_to_PEM_cert(der))
    bundle.close()
    return bundle.name


def _find_download_link(session, page_url: str, extension: str, file_hint: str | None) -> str:
    """Lấy link tải file (.pdf/.docx) từ trang văn bản trên Công báo."""
    page = session.get(page_url, timeout=30)
    page.raise_for_status()
    links = {
        html.unescape(match)
        for match in re.findall(r'href="(https://g7\.cdnchinhphu\.vn/api/download/stream[^"]+)"', page.text)
    }
    matches = [link for link in links if link.lower().endswith(extension)]
    if file_hint:
        matches = [link for link in matches if file_hint in unquote(link.split("file_name=")[-1])]
    if len(matches) != 1:
        raise ValueError(f"Expected 1 {extension} link, found {len(matches)}")
    return matches[0]


def download_documents() -> None:
    """Tải các văn bản trong LEGAL_DOCUMENTS vào DATA_DIR; bỏ qua file đã tải."""
    import requests

    session = requests.Session()
    session.headers.update(HEADERS)
    ca_bundle = None

    for doc in LEGAL_DOCUMENTS:
        target = DATA_DIR / doc["filename"]
        if target.exists():
            print(f"Skip (exists): {target.name}")
            continue
        try:
            ca_bundle = ca_bundle or _build_ca_bundle(session)
            extension = target.suffix.lower()
            link = _find_download_link(session, doc["page_url"], extension, doc.get("file_hint"))
            response = session.get(link, timeout=180, verify=ca_bundle)
            response.raise_for_status()
            if not response.content.startswith(FILE_SIGNATURES[extension]):
                raise ValueError(f"Response is not a {extension} file")
            target.write_bytes(response.content)
            print(f"Saved: {target.name} ({len(response.content) // 1024} KB)")
        except Exception as error:
            print(f"Failed: {doc['filename']} — {error}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
