"""Trợ lý AI của giáo viên: tìm kiếm & tổng hợp tài liệu bài giảng trong các lớp mình dạy, hoặc tài liệu tìm trên Google,
luôn có trích nguồn."""
import json
import logging
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import llm, websearch
from app.core.config import settings
from app.core.tenancy import search_teacher_chunks
from app.db import SessionLocal
from app.ingestion.pipeline import source_label
from app.models import Classroom, Document, DocumentPage, LectureChunk, TeacherAIMessage

from .chat import VN_TZ, _sse
from .prompts import TEACHER_ASSISTANT, TEACHER_TASKS, TEACHER_WEB_ASSISTANT, WEB_QUERY
from .tutor import CITE_RE, citations

log = logging.getLogger(__name__)
HISTORY_TURNS = 4
SEARCH_K = 14
FULL_DOC_CHARS = 30_000  # tóm tắt cả tài liệu: đưa tối đa ngần này ký tự cho model
WHOLE_DOC_TASKS = {"summary", "outline", "quiz", "lesson"}
WEB_RESULTS = 8   # số kết quả Google lấy về
WEB_READ = 5      # số trang đầu được đọc toàn văn (còn lại dùng đoạn trích của Google)


@dataclass
class AssistantPlan:
    teacher_id: str
    task: str
    system: str
    messages: list[dict]
    chunks: list[dict]
    truncated: bool = False
    web: list[dict] | None = None  # nguồn Google: [{label, title, url}]; None = tài liệu lớp
    query: str = ""


def _check_quota(db: Session, teacher_id: str) -> None:
    start = datetime.now(VN_TZ).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    used = db.scalar(select(func.count()).select_from(TeacherAIMessage).where(
        TeacherAIMessage.teacher_id == teacher_id, TeacherAIMessage.role == "user", TeacherAIMessage.created_at >= start))
    if used >= settings.teacher_ai_daily_limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"Đã dùng hết {settings.teacher_ai_daily_limit} lượt Trợ lý AI hôm nay. Lượt được làm mới lúc 0 giờ.")


def _chunk_dict(c: LectureChunk) -> dict:
    return {"source_label": c.source_label, "document_id": c.document_id, "page_number": c.page_number, "text": c.text}


def _whole_documents(db: Session, docs: list[Document]) -> tuple[list[dict], bool]:
    """Các trang của tài liệu được chọn (để tóm tắt cả tài liệu thay vì chỉ vài đoạn tìm được)."""
    out, total, truncated = [], 0, False
    for d in docs:
        for p in db.scalars(select(DocumentPage).where(DocumentPage.document_id == d.id).order_by(DocumentPage.page_number)):
            if total + len(p.text) > FULL_DOC_CHARS:
                truncated = True
                break
            total += len(p.text)
            out.append({"source_label": source_label(d.file_name, p.page_number), "document_id": d.id,
                        "page_number": p.page_number, "text": p.text})
        if truncated:
            break
    return out, truncated


def plan_assistant(db: Session, *, teacher_id: str, question: str, task: str,
                   classes: list[Classroom], docs: list[Document]) -> AssistantPlan:
    question = question.strip()
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Yêu cầu trống")
    if not llm.provider_ready(llm.Task.CHAT):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Trợ lý AI chưa được cấu hình khoá API.")
    _check_quota(db, teacher_id)

    truncated = False
    if docs and task in WHOLE_DOC_TASKS:
        chunks, truncated = _whole_documents(db, docs)
    else:
        found = search_teacher_chunks(db, teacher_id, [c.id for c in classes], question, k=SEARCH_K,
                                      document_ids=[d.id for d in docs] or None)
        chunks = [_chunk_dict(c) for c in found]

    names = {c.id: c.name for c in classes}
    doc_class = dict(db.execute(select(Document.id, Document.class_id).where(Document.id.in_({c["document_id"] for c in chunks}))).all())
    body = "\n".join(
        f'<doan nguon="{c["source_label"]}" lop="{names.get(doc_class.get(c["document_id"]), "")}">\n{c["text"]}\n</doan>'
        for c in chunks)
    system = (f"{TEACHER_ASSISTANT}\n\n{TEACHER_TASKS.get(task, TEACHER_TASKS['ask'])}"
              f"\n\n<tai_lieu>\n{body or '(không tìm thấy đoạn tài liệu nào liên quan)'}\n</tai_lieu>")
    if truncated:
        system += "\n\nLưu ý: tài liệu dài, chỉ phần đầu được đưa vào; hãy nói rõ bản tổng hợp dựa trên phần đầu tài liệu."

    return AssistantPlan(teacher_id=teacher_id, task=task, system=system,
                         messages=_record_question(db, teacher_id, task, question), chunks=chunks, truncated=truncated)


def _record_question(db: Session, teacher_id: str, task: str, question: str) -> list[dict]:
    """Lưu câu hỏi, trả về vài lượt hội thoại gần nhất + câu hỏi mới để gửi model."""
    rows = list(db.scalars(select(TeacherAIMessage).where(TeacherAIMessage.teacher_id == teacher_id)
                           .order_by(TeacherAIMessage.created_at.desc()).limit(HISTORY_TURNS * 2)))
    history = [{"role": m.role, "content": m.content} for m in reversed(rows)]
    db.add(TeacherAIMessage(teacher_id=teacher_id, role="user", task=task, content=question))
    db.commit()
    return [*history, {"role": "user", "content": question}]


# ---------- Tổng hợp tài liệu tìm trên Google ----------
def web_query(question: str) -> str:
    """Rút yêu cầu dài của giáo viên thành câu truy vấn Google; lỗi thì dùng nguyên văn."""
    try:
        q = str(llm.complete_json(llm.Task.CHAT, WEB_QUERY, [{"role": "user", "content": question}], max_tokens=100)
                .get("query") or "").strip()
    except Exception:  # noqa: BLE001
        q = ""
    return (q or question)[:200]


def plan_web_assistant(db: Session, *, teacher_id: str, question: str, task: str) -> AssistantPlan:
    question = question.strip()
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Yêu cầu trống")
    if not websearch.enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Tìm kiếm Google chưa được bật: quản trị viên cần thêm SERPER_API_KEY vào file .env.")
    if not llm.provider_ready(llm.Task.CHAT):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Trợ lý AI chưa được cấu hình khoá API.")
    _check_quota(db, teacher_id)

    query = web_query(question)
    try:
        results = websearch.search_and_read(query, num=WEB_RESULTS, read=WEB_READ)
    except websearch.WebSearchError as e:
        log.warning("tìm Google lỗi: %s", e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Không tìm được trên Google: {e}") from e

    sources, pages = [], []
    for i, r in enumerate(results, 1):
        label = f"Web {i} - {r.domain}"
        sources.append({"label": label, "title": r.title, "url": r.url})
        body = re.sub(r"</?\s*(trang|ket_qua_google)", "‹thẻ›", r.content or r.snippet, flags=re.I)
        pages.append(f'<trang nguon="{label}" tieu_de="{_attr(r.title)}">\n{body}\n</trang>')
    system = (f"{TEACHER_WEB_ASSISTANT}\n\n{TEACHER_TASKS.get(task, TEACHER_TASKS['ask'])}"
              f"\n\n<ket_qua_google truy_van=\"{_attr(query)}\">\n"
              f"{chr(10).join(pages) or '(Google không trả về kết quả nào)'}\n</ket_qua_google>")
    return AssistantPlan(teacher_id=teacher_id, task=task, system=system,
                         messages=_record_question(db, teacher_id, task, question), chunks=[], web=sources, query=query)


def _attr(s: str) -> str:
    return s.replace('"', "'").replace("<", "‹").replace(">", "›")


def web_citations(answer: str, sources: list[dict]) -> list[dict]:
    """Chỉ giữ thẻ nguồn trỏ đúng trang Google đã trả về (chặn link bịa)."""
    allowed = {s["label"]: s for s in sources}
    out, seen = [], set()
    for label in CITE_RE.findall(answer):
        s = allowed.get(label)
        if s and label not in seen:
            seen.add(label)
            out.append({"label": label, "url": s["url"], "title": s["title"], "document_id": "", "page_number": 0})
    return out


def assistant_stream(plan: AssistantPlan) -> Iterator[str]:
    start = {"type": "start", "mode": "teacher", "route": "answer", "truncated": plan.truncated,
             "sources": len(plan.web) if plan.web is not None else len(plan.chunks)}
    if plan.web is not None:
        start |= {"web_sources": plan.web, "query": plan.query}
    yield _sse(start)
    text, failed = "", False
    try:
        for piece in llm.stream(llm.Task.CHAT, plan.system, plan.messages, max_tokens=4000):
            text += piece
            yield _sse({"type": "delta", "text": piece})
    except Exception as e:  # noqa: BLE001
        log.exception("trợ lý giáo viên lỗi")
        failed = True
        yield _sse({"type": "error", "message": "Trợ lý AI đang bận hoặc lỗi kết nối, thử lại sau ít phút."})
        text = text or f"(lỗi: {type(e).__name__})"
    cites = web_citations(text, plan.web) if plan.web is not None else citations(text, plan.chunks)
    db = SessionLocal()
    try:
        db.add(TeacherAIMessage(teacher_id=plan.teacher_id, role="assistant", task=plan.task, content=text,
                                citations=json.dumps(cites, ensure_ascii=False)))
        db.commit()
    finally:
        db.close()
    if not failed:
        yield _sse({"type": "done", "citations": cites, "mode": "teacher", "route": "answer"})


# ---------- Tìm kiếm (không cần gọi model) ----------
def _fold(s: str) -> str:
    t = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(ch for ch in t if unicodedata.category(ch) != "Mn")


def snippet(text: str, query: str, width: int = 320) -> str:
    """Đoạn trích quanh chỗ khớp đầu tiên (so khớp không dấu)."""
    folded = _fold(text)
    if len(folded) != len(text):  # chuẩn hoá làm lệch vị trí: lấy phần đầu
        return text[:width] + ("…" if len(text) > width else "")
    pos = -1
    for w in sorted(re.findall(r"\w+", _fold(query)), key=len, reverse=True):
        if len(w) >= 3 and (pos := folded.find(w)) >= 0:
            break
    start = max(0, pos - width // 3) if pos >= 0 else 0
    end = min(len(text), start + width)
    return ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")
