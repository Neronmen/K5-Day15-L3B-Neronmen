"""Nạp tri thức: bóc tách file → chia đoạn kèm số trang → (vector hoá) → lưu gắn tenant.

Chạy ở worker (Celery) hoặc chạy nền trong API khi TASK_BACKEND=inline.
"""
import io
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete

from app.core import llm, storage
from app.db import SessionLocal
from app.models import Classroom, DocStatus, Document, DocumentPage, LectureChunk, Notification

log = logging.getLogger(__name__)
PAGE_BREAK = re.compile(r"^\s*(?:---\s*page\s*---|\f)\s*$", re.I | re.M)
WORD_PART_CHARS = 3000


@dataclass
class PageText:
    page_number: int
    text: str


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pdf_docling(data: bytes) -> list[PageText] | None:
    """Docling giữ cấu trúc bảng/công thức tốt hơn. Dùng nếu đã cài (pip install docling)."""
    try:
        from docling.datamodel.base_models import DocumentStream
        from docling.document_converter import DocumentConverter
    except ImportError:
        return None
    result = DocumentConverter().convert(DocumentStream(name="doc.pdf", stream=io.BytesIO(data)))
    doc = result.document
    pages = []
    for page_no in sorted(doc.pages):
        md = doc.export_to_markdown(page_no=page_no)
        pages.append(PageText(page_no, _clean(md)))
    return pages


def _pdf_pypdf(data: bytes) -> list[PageText]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return [PageText(i + 1, _clean(p.extract_text() or "")) for i, p in enumerate(reader.pages)]


def _pptx(data: bytes) -> list[PageText]:
    from pptx import Presentation

    pages = []
    for i, slide in enumerate(Presentation(io.BytesIO(data)).slides, start=1):
        parts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                parts.append(shape.text_frame.text)
            if getattr(shape, "has_table", False) and shape.has_table:
                for row in shape.table.rows:
                    parts.append(" | ".join(c.text for c in row.cells))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            parts.append("Ghi chú: " + slide.notes_slide.notes_text_frame.text)
        pages.append(PageText(i, _clean("\n".join(parts))))
    return pages


def _split_parts(text: str) -> list[PageText]:
    """Word/Markdown không có trang cố định: dùng dấu ngắt trang nếu có, không thì chia ~3000 ký tự theo đoạn văn."""
    if PAGE_BREAK.search(text):
        return [PageText(i, _clean(t)) for i, t in enumerate(PAGE_BREAK.split(text), start=1) if t.strip()]
    pages, buf = [], ""
    for para in text.split("\n"):
        if len(buf) + len(para) > WORD_PART_CHARS and buf:
            pages.append(PageText(len(pages) + 1, _clean(buf)))
            buf = ""
        buf += para + "\n"
    if buf.strip():
        pages.append(PageText(len(pages) + 1, _clean(buf)))
    return pages


def _docx(data: bytes) -> list[PageText]:
    import docx

    d = docx.Document(io.BytesIO(data))
    lines = []
    for p in d.paragraphs:
        # Ngắt trang thủ công trong Word → giữ làm ranh giới trang
        if 'w:br w:type="page"' in p._p.xml:
            lines.append("---page---")
        lines.append(p.text)
    for t in d.tables:
        for row in t.rows:
            lines.append(" | ".join(c.text for c in row.cells))
    return _split_parts("\n".join(lines))


def extract_pages(data: bytes, file_name: str) -> list[PageText]:
    ext = Path(file_name).suffix.lower()
    if ext == ".pdf":
        pages = _pdf_docling(data) or _pdf_pypdf(data)
    elif ext == ".pptx":
        pages = _pptx(data)
    elif ext == ".docx":
        pages = _docx(data)
    elif ext in (".md", ".txt"):
        pages = _split_parts(data.decode("utf-8-sig", errors="replace"))
    else:
        raise ValueError(f"Chưa hỗ trợ đọc file {ext}. Hãy lưu lại dưới dạng PDF, .docx hoặc .pptx.")
    return [p for p in pages if p.text]


def unit_label(file_name: str) -> str:
    ext = Path(file_name).suffix.lower()
    return {".pptx": "Slide", ".docx": "Phần", ".md": "Trang", ".txt": "Phần"}.get(ext, "Trang")


def source_label(file_name: str, page_number: int) -> str:
    """Thẻ nguồn hiển thị cho học sinh: 'Tên_file - Trang X'."""
    return f"{file_name} - {unit_label(file_name)} {page_number}"


def chunk_pages(pages: list[PageText], max_chars: int = 1200, overlap: int = 200) -> list[PageText]:
    """Chia đoạn trong phạm vi từng trang để mỗi đoạn luôn có đúng một số trang. Cắt ở ranh giới câu/dòng nếu được."""
    chunks: list[PageText] = []
    for page in pages:
        text = page.text
        start = 0
        while start < len(text):
            end = min(len(text), start + max_chars)
            if end < len(text):
                cut = max(text.rfind("\n", start + max_chars // 2, end), text.rfind(". ", start + max_chars // 2, end))
                if cut > start:
                    end = cut + 1
            piece = text[start:end].strip()
            if piece:
                chunks.append(PageText(page.page_number, piece))
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks


def save_pages_and_chunks(db, doc: Document, cls: Classroom, pages: list[PageText]) -> int:
    db.execute(delete(LectureChunk).where(LectureChunk.document_id == doc.id))
    db.execute(delete(DocumentPage).where(DocumentPage.document_id == doc.id))
    for p in pages:
        db.add(DocumentPage(document_id=doc.id, page_number=p.page_number, text=p.text))
    chunks = chunk_pages(pages)
    vectors = None
    if chunks and llm.embeddings_enabled():
        vectors = []
        for i in range(0, len(chunks), 64):
            vectors.extend(llm.embed([c.text for c in chunks[i:i + 64]]) or [])
    for i, c in enumerate(chunks):
        db.add(LectureChunk(
            document_id=doc.id, page_number=c.page_number,
            teacher_id=cls.teacher_id, class_id=cls.id, subject_id=cls.subject_id,  # Rule 2: đủ 3 khoá tenant
            source_label=source_label(doc.file_name, c.page_number), text=c.text,
            embedding=vectors[i] if vectors else None,
        ))
    return len(chunks)


def ingest_document(document_id: str) -> None:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return
        cls = db.get(Classroom, doc.class_id)
        try:
            pages = extract_pages(storage.read_file(doc.file_key), doc.file_name)
            if not pages:
                raise ValueError("Không đọc được chữ trong tài liệu (có thể là bản scan ảnh). Hãy tải bản PDF có chữ.")
            n = save_pages_and_chunks(db, doc, cls, pages)
            doc.status, doc.page_count, doc.error = DocStatus.READY.value, max(p.page_number for p in pages), None
            msg = {"document_id": doc.id, "file_name": doc.file_name, "class_id": cls.id, "chunks": n}
            db.add(Notification(user_id=cls.teacher_id, kind="doc_ready", payload=json.dumps(msg, ensure_ascii=False)))
        except Exception as e:  # noqa: BLE001 - lỗi nào cũng phải báo lại cho giáo viên
            log.exception("ingest_document %s lỗi", document_id)
            db.rollback()
            doc = db.get(Document, document_id)
            doc.status, doc.error = DocStatus.FAILED.value, str(e)[:500]
            db.add(Notification(user_id=cls.teacher_id, kind="doc_failed",
                                payload=json.dumps({"document_id": doc.id, "file_name": doc.file_name, "class_id": cls.id,
                                                    "error": doc.error}, ensure_ascii=False)))
        db.commit()
    finally:
        db.close()
