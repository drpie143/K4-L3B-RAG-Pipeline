"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert tài liệu legal thật; không sinh nội dung mẫu khi thư mục rỗng."""
    legal_dir = LANDING_DIR / "legal"
    paths = [
        path for path in sorted(legal_dir.iterdir())
        if path.suffix.lower() in {".pdf", ".doc", ".docx"}
    ]
    if not paths:
        return

    from markitdown import MarkItDown

    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    for path in paths:
        result = converter.convert(str(path))
        content = result.text_content.strip()
        if not content:
            raise ValueError(f"Conversion produced empty content: {path}")
        markdown = _front_matter(
            title=path.stem.replace("_", " "),
            source=path.name,
            doc_type="legal",
            url="",
        ) + content
        (output_dir / f"{path.stem}.md").write_text(markdown, encoding="utf-8")


def convert_news_articles() -> None:
    """Convert các JSON crawl thật và giữ metadata nguồn trong front matter."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    required = {"url", "title", "date_crawled", "content_markdown"}
    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = required - data.keys()
        if missing:
            raise ValueError(f"{path.name} is missing fields: {sorted(missing)}")
        if any(not str(data[key]).strip() for key in required):
            raise ValueError(f"{path.name} contains empty required fields")
        markdown = _front_matter(
            title=data["title"],
            source=path.name,
            doc_type="news",
            url=data["url"],
            date_crawled=data["date_crawled"],
        ) + data["content_markdown"].strip()
        (output_dir / f"{path.stem}.md").write_text(markdown, encoding="utf-8")


def _front_matter(**metadata: str) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        safe_value = str(value).replace("\r", " ").replace("\n", " ").replace('"', "'")
        lines.append(f'{key}: "{safe_value}"')
    lines.extend(["---", ""])
    return "\n".join(lines) + "\n"


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
