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

Mỗi file Markdown đầu ra có front matter (title, source, url, doc_type, ngày...)
để Task 4 đọc metadata. Văn bản pháp luật được chuẩn hóa tiêu đề:
"## Chương ...", "## Mục ...", "### Điều ..." để chunk theo Điều về sau.
"""

import json
import re
import tempfile
import zipfile
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

LEGAL_EXTENSIONS = {".pdf", ".docx"}

# Dòng rác của bản PDF Công báo: header trang, số trang, ghi chú nối số báo, bìa sau.
PDF_NOISE_PATTERNS = [
    r"^\d*\s*CÔNG BÁO/Số .*$",
    r"^\d+$",
    r"^VĂN BẢN QUY PHẠM PHÁP LUẬT$",
    r"^\(Tiếp theo Công báo .*\)$",
    r"^\(Xem tiếp Công báo .*\)$",
    r"^[\\_]+$",
    r"^aky\]$",
]
PDF_BACK_COVER = "VĂN PHÒNG CHÍNH PHỦ XUẤT BẢN"

# Dòng bắt đầu một đoạn mới trong văn bản pháp luật.
PARAGRAPH_START = re.compile(
    r"^(Chương [IVXLC]+\b|Mục \d+\b|Điều \d+[a-z]?\.|Phụ lục|PHỤ LỤC|\d+[a-z]?[.-]\s|[a-zđ]\)\s|[-+•]\s"
    r"|Căn cứ |Theo đề nghị |Số: |NGHỊ ĐỊNH$|TM\. |KT\. |Nơi nhận)"
)


def _front_matter(fields: dict) -> str:
    """Front matter dạng YAML; giá trị được JSON-quote để an toàn với dấu ':'."""
    lines = [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items() if value]
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def _legal_metadata() -> dict[str, dict]:
    from src.task1_collect_legal_docs import LEGAL_DOCUMENTS

    return {Path(doc["filename"]).stem: doc for doc in LEGAL_DOCUMENTS}


def _normalized_docx(path: Path, workdir: Path) -> Path:
    """DOCX của Công báo dùng '\\' trong đường dẫn zip; đóng gói lại cho chuẩn OOXML."""
    source = zipfile.ZipFile(path)
    if not any("\\" in name for name in source.namelist()):
        return path
    fixed = workdir / path.name
    with zipfile.ZipFile(fixed, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            target.writestr(info.filename.replace("\\", "/"), source.read(info))
    return fixed


def _clean_docx_markdown(text: str) -> str:
    """Bỏ bảng quốc hiệu/chữ ký, chuẩn hóa tiêu đề Chương/Mục/Điều."""
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    output: list[str] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        plain = re.sub(r"\*+", "", block).strip()
        index += 1
        if block.startswith("|") and re.search(r"XÃ HỘI CHỦ NGHĨA|TM\. CHÍNH PHỦ|Nơi nhận", plain):
            continue
        if re.fullmatch(r"[\\_\s]+", plain):
            continue
        if re.fullmatch(r"(Chương [IVXLC]+|Mục \d+)", plain):
            # Tên chương có thể bị tách thành nhiều đoạn in đậm viết hoa liên tiếp.
            parts = []
            while index < len(blocks) and re.fullmatch(r"\*\*[^*]+\*\*", blocks[index]):
                part = blocks[index].strip("* ")
                if not part.isupper():
                    break
                parts.append(part)
                index += 1
            title = " ".join(parts)
            output.append(f"## {plain}" + (f". {title}" if title else ""))
            continue
        if block.startswith("**Điều ") or plain in ("Phụ lục", "PHỤ LỤC"):
            level = "##" if plain.lower() == "phụ lục" else "###"
            output.append(level + " " + " ".join(plain.split()))
            continue
        output.append(block)
    return "\n\n".join(output)


def _clean_pdf_markdown(text: str) -> str:
    """Bỏ header Công báo, nối các dòng bị ngắt thành đoạn, chuẩn hóa tiêu đề."""
    text = text.split(PDF_BACK_COVER)[0]
    noise = re.compile("|".join(PDF_NOISE_PATTERNS))
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line and not noise.match(line)]

    # Phụ lục sau chữ ký của bản PDF là biểu mẫu tờ khai trống; bảng bị trích lộn xộn nên bỏ.
    signed = next((i for i, line in enumerate(lines) if line.startswith("TM. CHÍNH PHỦ")), None)
    if signed is not None:
        appendix = next(
            (i for i in range(signed, len(lines)) if re.match(r"(Phụ lục|PHỤ LỤC|Mẫu số)", lines[i])),
            None,
        )
        lines = lines[:appendix]

    paragraphs: list[str] = []
    heading = False
    for line in lines:
        previous = paragraphs[-1] if paragraphs else ""
        starts_new = (
            not paragraphs
            or PARAGRAPH_START.match(line)
            or (previous.endswith((".", ";", ":", "?", "!")) and line[0].isupper())
            or (heading and line[0].isupper() and not previous.endswith("-"))
        )
        if starts_new:
            paragraphs.append(line)
        elif previous.endswith("-") and not previous.endswith(" -"):
            paragraphs[-1] = previous + line
        else:
            paragraphs[-1] = previous + " " + line
        heading = bool(re.match(r"(Chương [IVXLC]+|Mục \d+|Điều \d+[a-z]?\.)", paragraphs[-1]))

    output: list[str] = []
    index = 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        index += 1
        chapter = re.fullmatch(r"(Chương [IVXLC]+|Mục \d+)(.*)", paragraph)
        if chapter:
            title = chapter.group(2).strip()
            # Tên chương viết hoa thường nằm ở đoạn kế tiếp; đôi khi PDF trích nó ra trước "Chương".
            if not title and index < len(paragraphs) and paragraphs[index].isupper():
                title = paragraphs[index]
                index += 1
            elif not title and output and output[-1].isupper() and not output[-1].startswith("#"):
                title = output.pop()
            output.append(f"## {chapter.group(1)}" + (f". {title}" if title else ""))
        elif re.match(r"Điều \d+[a-z]?\. ", paragraph):
            output.append(f"### {paragraph}")
        elif paragraph in ("Phụ lục", "PHỤ LỤC"):
            output.append("## Phụ lục")
        else:
            output.append(paragraph)
    return "\n\n".join(output)


def _remove_stale_outputs(output_dir: Path, expected: set[str]) -> None:
    """Xóa file .md không còn file nguồn tương ứng (tránh trùng khi đổi tên nguồn)."""
    for path in output_dir.glob("*.md"):
        if path.name not in expected:
            path.unlink()
            print(f"Removed stale: {path.relative_to(OUTPUT_DIR)}")


def convert_legal_docs() -> None:
    """Convert PDF/DOCX trong landing/legal sang standardized/legal."""
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    metadata = _legal_metadata()
    written: set[str] = set()

    with tempfile.TemporaryDirectory() as workdir:
        for path in sorted(legal_dir.iterdir()):
            suffix = path.suffix.lower()
            if suffix not in LEGAL_EXTENSIONS:
                continue
            if suffix == ".docx":
                raw = converter.convert(str(_normalized_docx(path, Path(workdir)))).text_content
                body = _clean_docx_markdown(raw)
            else:
                body = _clean_pdf_markdown(converter.convert(str(path)).text_content)

            if len(body.strip()) < 200:
                print(f"Skip (no text, scanned?): {path.name}")
                continue

            doc = metadata.get(path.stem, {})
            title = doc.get("title", path.stem)
            header = _front_matter({
                "title": title,
                "source": path.name,
                "doc_type": "legal",
                "number": doc.get("number"),
                "url": doc.get("page_url"),
                "issued": doc.get("issued"),
                "effective": doc.get("effective"),
            })
            output = output_dir / f"{path.stem}.md"
            output.write_text(f"{header}# {title}\n\n{body}\n", encoding="utf-8")
            written.add(output.name)
            print(f"Saved: legal/{output.name} ({len(body)} chars)")

    _remove_stale_outputs(output_dir, written)


def convert_news_articles() -> None:
    """Convert JSON trong landing/news sang standardized/news."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    written: set[str] = set()

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        body = data.get("content_markdown", "").strip()
        if len(body) < 200:
            print(f"Skip (empty): {path.name}")
            continue
        header = _front_matter({
            "title": data["title"],
            "source": path.name,
            "doc_type": "news",
            "url": data["url"],
            "date_published": data.get("date_published"),
            "date_crawled": data["date_crawled"],
        })
        output = output_dir / f"{path.stem}.md"
        output.write_text(header + body + "\n", encoding="utf-8")
        written.add(output.name)
        print(f"Saved: news/{output.name} ({len(body)} chars)")

    _remove_stale_outputs(output_dir, written)


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
