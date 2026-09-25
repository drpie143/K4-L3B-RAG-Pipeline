"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL (nhóm dùng requests + BeautifulSoup thay cho Crawl4AI,
       vì các trang nguồn trả HTML tĩnh, không cần trình duyệt).
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

-> Dùng Firecrawl or bất cứ công cụ nào bạn quen
"""

import json
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Bài diễn giải các văn bản ở task 1 (baochinhphu.vn, xaydungchinhsach.chinhphu.vn, vnexpress.net).
ARTICLE_URLS = [
    # Nghị định 141/2026: nâng ngưỡng không phải nộp thuế lên 1 tỷ đồng
    "https://baochinhphu.vn/chinh-thuc-nang-nguong-chiu-thue-voi-ho-kinh-doanh-len-01-ty-dong-nam-ap-dung-tu-1-1-2026-102260429185517215.htm",
    # Đăng ký hộ kinh doanh (Nghị định 168/2025)
    "https://baochinhphu.vn/quy-dinh-moi-ve-dang-ky-ho-kinh-doanh-102250702150908133.htm",
    # Thuế hộ kinh doanh từ 1/1/2026 (bài tháng 1/2026, còn nêu ngưỡng cũ)
    "https://baochinhphu.vn/nhieu-thay-doi-ve-thue-doi-voi-ca-nhan-va-ho-kinh-doanh-102260106104740091.htm",
    "https://vnexpress.net/co-quan-thue-huong-dan-ho-kinh-doanh-ke-khai-nop-thue-tu-2026-5013509.html",
    # Thuế trên sàn thương mại điện tử (Nghị định 117/2025)
    "https://baochinhphu.vn/quy-dinh-quan-ly-thue-doi-voi-ho-ca-nhan-kinh-doanh-tren-nen-tang-thuong-mai-dien-tu-102250611153921023.htm",
    # Hóa đơn điện tử (Nghị định 254/2026, Thông tư 91/2026)
    "https://xaydungchinhsach.chinhphu.vn/nhung-diem-moi-cua-nghi-dinh-254-2026-nd-cp-va-thong-tu-91-2026-tt-btc-ve-hoa-don-dien-tu-chung-tu-dien-tu-119260717143502375.htm",
    # Luật Quản lý thuế 108/2025/QH15
    "https://xaydungchinhsach.chinhphu.vn/nhung-diem-moi-noi-dung-trong-tam-cua-luat-quan-ly-thue-so-108-2025-qh15-119260713105610538.htm",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (K4-RAG-Lab; educational crawler)"}

# Vùng nội dung chính của từng site (chinhphu.vn dùng chung template).
CONTENT_SELECTORS = ["div.detail-content", "article.fck_detail"]
SAPO_SELECTORS = ["h2.detail-sapo", "p.description"]
DATE_SELECTORS = [
    "meta[property='article:published_time']",
    "meta[itemprop='datePublished']",
    "meta[name='pubdate']",
]
# Khối không phải nội dung bài: ảnh, video, bài liên quan, quảng cáo.
NOISE_SELECTORS = [
    "script", "style", "figure", "video", "iframe", "noscript",
    "div.VCSortableInPreviewMode[type='RelatedNewsBox']",
    "div[type='RelatedOneNews']", "div.box-tinlienquanv2", "table.tplCaption",
]


def _inline_text(node: Tag) -> str:
    """Lấy text của một khối, giữ chữ đậm dạng **...**."""
    parts = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name in ("strong", "b"):
            text = child.get_text(" ", strip=True)
            parts.append(f"**{text}**" if text else "")
        elif child.name == "br":
            parts.append("\n")
        elif isinstance(child, Tag):
            parts.append(_inline_text(child))
    return " ".join("".join(parts).split(" ")).strip()


def _table_to_markdown(table: Tag) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True).replace("|", "/") for c in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def html_to_markdown(content: Tag) -> str:
    """Chuyển vùng nội dung bài viết sang Markdown đơn giản."""
    blocks = []
    for node in content.find_all(["h2", "h3", "h4", "p", "li", "table"]):
        # Bỏ phần tử nằm trong bảng/list cha đã được xử lý.
        if node.name != "table" and node.find_parent("table"):
            continue
        if node.name == "p" and node.find_parent("li"):
            continue
        if node.name == "table":
            text = _table_to_markdown(node)
        else:
            text = _inline_text(node)
            if node.name in ("h2", "h3", "h4"):
                text = "#" * int(node.name[1]) + " " + text.strip("* ")
            elif node.name == "li":
                text = "- " + text
        if text.strip():
            blocks.append(text.strip())
    return "\n\n".join(blocks)


def _first(soup: BeautifulSoup, selectors: list[str]) -> Tag | None:
    for selector in selectors:
        found = soup.select_one(selector)
        if found:
            return found
    return None


def crawl_article(url: str) -> dict:
    """Tải một URL và trả về dict theo schema của task."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "lxml")

    content = _first(soup, CONTENT_SELECTORS)
    if content is None:
        raise RuntimeError("Không tìm thấy vùng nội dung bài viết")
    for selector in NOISE_SELECTORS:
        for noise in content.select(selector):
            noise.decompose()

    og_title = soup.find("meta", property="og:title")
    title = og_title["content"].strip() if og_title else soup.title.get_text(strip=True)
    date_meta = _first(soup, DATE_SELECTORS)
    sapo = _first(soup, SAPO_SELECTORS)

    body = html_to_markdown(content)
    parts = [f"# {title}"]
    # VnExpress lặp lại sapo ở đoạn đầu thân bài.
    if sapo and sapo.get_text(" ", strip=True) not in body[:500]:
        parts.append(sapo.get_text(" ", strip=True))
    parts.append(body)

    return {
        "url": url,
        "title": title,
        "date_published": date_meta.get("content") if date_meta else None,
        "date_crawled": datetime.now().astimezone().isoformat(timespec="seconds"),
        "content_markdown": "\n\n".join(parts),
    }


def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output.name} ({len(article['content_markdown'])} chars) — {article['title']}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    crawl_all()
