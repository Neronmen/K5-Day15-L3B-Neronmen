"""Tìm kiếm Google cho Trợ lý AI giáo viên: lấy kết quả Google qua Serper.dev rồi đọc nội dung các trang đầu.

Vì sao Serper mà không dùng Google Custom Search JSON API: Google đã đóng API đó với khách hàng mới
và ngừng hẳn từ 01/01/2027. Serper trả đúng kết quả tìm kiếm Google dưới dạng JSON.
"""
import ipaddress
import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)
SERPER_URL = "https://google.serper.dev/search"
MAX_BYTES = 3_000_000       # không tải trang/file lớn hơn
PAGE_CHARS = 5_000          # ký tự tối đa lấy từ mỗi trang
FETCH_TIMEOUT = 8.0
MAX_REDIRECTS = 3
USER_AGENT = "Mozilla/5.0 (compatible; MinutesStudyBot/1.0; teaching-assistant)"


class WebSearchError(Exception):
    pass


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str
    content: str = ""

    @property
    def domain(self) -> str:
        host = urlparse(self.url).hostname or ""
        return host.removeprefix("www.")


def enabled() -> bool:
    return settings.web_search_provider == "serper" and bool(settings.serper_api_key)


def google_search(query: str, num: int = 8) -> list[WebResult]:
    """Kết quả Google (tự nhiên, bỏ quảng cáo) cho câu truy vấn, ưu tiên tiếng Việt / Việt Nam."""
    if not enabled():
        raise WebSearchError("Chưa cấu hình SERPER_API_KEY")
    try:
        r = httpx.post(SERPER_URL, timeout=15.0,
                       headers={"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"},
                       json={"q": query, "num": num, "gl": settings.web_search_country, "hl": settings.web_search_language})
    except httpx.HTTPError as e:
        raise WebSearchError(f"Không gọi được dịch vụ tìm kiếm: {type(e).__name__}") from e
    if r.status_code in (401, 403):
        raise WebSearchError("Khoá SERPER_API_KEY không hợp lệ hoặc đã hết lượt")
    if r.status_code >= 400:
        raise WebSearchError(f"Dịch vụ tìm kiếm lỗi {r.status_code}")
    data = r.json()
    out, seen = [], set()
    for item in data.get("organic", []):
        url = item.get("link") or ""
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        out.append(WebResult(title=(item.get("title") or url)[:200], url=url, snippet=item.get("snippet") or ""))
    if box := data.get("answerBox"):
        if box.get("link") and box["link"] not in seen and (box.get("snippet") or box.get("answer")):
            out.insert(0, WebResult(title=box.get("title") or box["link"], url=box["link"],
                                    snippet=box.get("snippet") or box.get("answer") or ""))
    return out[:num]


# ---------- Đọc nội dung trang ----------
def _public_host(host: str) -> bool:
    """Chặn SSRF: chỉ cho phép tên miền phân giải ra địa chỉ IP công khai."""
    if not host or host == "localhost" or host.endswith((".local", ".internal", ".localhost")):
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global or ip.is_multicast:
            return False
    return True


def safe_url(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in ("http", "https") and p.port in (None, 80, 443) and not p.username and _public_host(p.hostname or "")


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form", "iframe", "template"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
        p.close()
    except Exception:  # noqa: BLE001 - HTML hỏng: lấy được bao nhiêu dùng bấy nhiêu
        pass
    lines = (re.sub(r"[ \t ]+", " ", ln).strip() for ln in "".join(p.parts).splitlines())
    # Bỏ dòng quá ngắn (menu, nút bấm) để còn lại phần nội dung chính
    return "\n".join(ln for ln in lines if len(ln) >= 25)


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    return "\n".join((pg.extract_text() or "") for pg in reader.pages[:8])


def fetch_text(url: str, max_chars: int = PAGE_CHARS) -> str:
    """Văn bản chính của trang web / file PDF; chuỗi rỗng nếu không đọc được."""
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
            for _ in range(MAX_REDIRECTS + 1):
                if not safe_url(url):
                    return ""
                with client.stream("GET", url) as r:
                    if r.is_redirect and r.headers.get("location"):
                        url = urljoin(url, r.headers["location"])
                        continue
                    if r.status_code != 200:
                        return ""
                    ctype = r.headers.get("content-type", "").lower()
                    if "html" not in ctype and "pdf" not in ctype and "text/plain" not in ctype:
                        return ""
                    buf = bytearray()
                    for chunk in r.iter_bytes():
                        buf += chunk
                        if len(buf) > MAX_BYTES:
                            return ""
                    if "pdf" in ctype:
                        text = _pdf_text(bytes(buf))
                    else:
                        raw = bytes(buf).decode(r.encoding or "utf-8", errors="replace")
                        text = raw if "text/plain" in ctype else html_to_text(raw)
                    return text[:max_chars].strip()
    except Exception as e:  # noqa: BLE001 - trang lỗi thì chỉ dùng đoạn trích của Google
        log.info("không đọc được %s: %s", url, type(e).__name__)
    return ""


def search_and_read(query: str, num: int = 8, read: int = 5) -> list[WebResult]:
    """Tìm Google rồi đọc song song nội dung `read` trang đầu (trang không đọc được vẫn giữ đoạn trích)."""
    results = google_search(query, num=num)
    with ThreadPoolExecutor(max_workers=max(1, read)) as pool:
        for res, text in zip(results[:read], pool.map(lambda r: fetch_text(r.url), results[:read])):
            res.content = text
    return results
