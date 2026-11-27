"""Trợ lý AI của giáo viên: tìm kiếm, tổng hợp tài liệu các lớp mình dạy hoặc tài liệu trên Google,
lưu bản tổng hợp thành tài liệu lớp."""
import json
import re
import unicodedata
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.agents.teacher_assistant import assistant_stream, plan_assistant, plan_web_assistant, snippet
from app.core import storage, websearch
from app.core.security import CurrentUser, require_teacher
from app.core.tenancy import search_teacher_chunks
from app.db import get_db
from app.ingestion.pipeline import unit_label
from app.models import Classroom, DocStatus, Document, DocumentPage, TeacherAIMessage
from app.routers.common import aware, document_out, owned_class
from app.schemas import ChatMessageOut, DocPage, DocumentOut
from app.tasks import enqueue_ingest

router = APIRouter(prefix="/teacher/assistant", tags=["trợ lý AI giáo viên"])
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
MAX_DOCS = 5

TaskT = Literal["ask", "summary", "outline", "quiz", "lesson"]


class ScopeIn(BaseModel):
    class_ids: list[str] = Field(default_factory=list, max_length=100)  # rỗng = mọi lớp đang dạy
    document_ids: list[str] = Field(default_factory=list, max_length=MAX_DOCS)


class SearchIn(ScopeIn):
    query: str = Field(min_length=1, max_length=500)


class AssistantChatIn(ScopeIn):
    question: str = Field(min_length=1, max_length=4000)
    task: TaskT = "ask"
    source: Literal["docs", "web"] = "docs"  # docs: tài liệu các lớp | web: tìm trên Google rồi tổng hợp


class SaveIn(BaseModel):
    class_id: str
    title: str = Field(min_length=1, max_length=150)
    content: str = Field(min_length=1, max_length=200_000)


class SourceDoc(BaseModel):
    id: str
    file_name: str
    page_count: int | None
    is_pdf: bool
    unit: str


class SourceClass(BaseModel):
    id: str
    name: str
    subject: str
    documents: list[SourceDoc]


class SearchHit(BaseModel):
    class_id: str
    class_name: str
    document_id: str
    file_name: str
    page_number: int
    source_label: str
    snippet: str


def _scope(db: Session, user: CurrentUser, body: ScopeIn) -> tuple[list[Classroom], list[Document]]:
    if body.class_ids:
        classes = [owned_class(db, user, cid) for cid in dict.fromkeys(body.class_ids)]
    else:
        classes = list(db.scalars(select(Classroom).where(Classroom.teacher_id == user.id)))
    ids = {c.id for c in classes}
    docs = []
    for did in dict.fromkeys(body.document_ids):
        d = db.get(Document, did)
        if not d or d.class_id not in ids:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu trong các lớp đã chọn")
        if d.status != DocStatus.READY.value:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{d.file_name} chưa xử lý xong")
        docs.append(d)
    return classes, docs


@router.get("/sources", response_model=list[SourceClass])
def sources(user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Các lớp và tài liệu đã sẵn sàng, để giáo viên chọn phạm vi tìm kiếm."""
    out = []
    for c in db.scalars(select(Classroom).where(Classroom.teacher_id == user.id).order_by(Classroom.name)):
        docs = db.scalars(select(Document).where(Document.class_id == c.id, Document.status == DocStatus.READY.value)
                          .order_by(Document.uploaded_at.desc()))
        out.append(SourceClass(id=c.id, name=c.name, subject=c.subject_id, documents=[
            SourceDoc(id=d.id, file_name=d.file_name, page_count=d.page_count,
                      is_pdf=d.file_name.lower().endswith(".pdf"), unit=unit_label(d.file_name)) for d in docs]))
    return out


class AssistantStatus(BaseModel):
    web_search: bool


@router.get("/status", response_model=AssistantStatus)
def assistant_status(user: CurrentUser = Depends(require_teacher)):
    """Các tính năng đang bật (để giao diện ẩn/hiện nút Tìm trên Google)."""
    return AssistantStatus(web_search=websearch.enabled())


@router.post("/search", response_model=list[SearchHit])
def search(body: SearchIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Tìm đoạn tài liệu khớp từ khoá trong các lớp đã chọn (không gọi model, không tốn lượt)."""
    classes, docs = _scope(db, user, body)
    names = {c.id: c.name for c in classes}
    hits = search_teacher_chunks(db, user.id, list(names), body.query, k=30, document_ids=[d.id for d in docs] or None)
    files = dict(db.execute(select(Document.id, Document.file_name).where(Document.id.in_({h.document_id for h in hits}))).all())
    return [SearchHit(class_id=h.class_id, class_name=names.get(h.class_id, ""), document_id=h.document_id,
                      file_name=files.get(h.document_id, ""), page_number=h.page_number, source_label=h.source_label,
                      snippet=snippet(h.text, body.query)) for h in hits]


@router.post("/chat")
def chat(body: AssistantChatIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Hỏi / tóm tắt / đề cương / câu hỏi ôn tập / dàn ý bài giảng từ tài liệu đã chọn hoặc từ Google. Stream SSE."""
    if body.source == "web":
        plan = plan_web_assistant(db, teacher_id=user.id, question=body.question, task=body.task)
        return StreamingResponse(assistant_stream(plan), media_type="text/event-stream", headers=SSE_HEADERS)
    classes, docs = _scope(db, user, body)
    if not classes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa có lớp nào. Tạo lớp và tải tài liệu trước.")
    plan = plan_assistant(db, teacher_id=user.id, question=body.question, task=body.task, classes=classes, docs=docs)
    return StreamingResponse(assistant_stream(plan), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/history", response_model=list[ChatMessageOut])
def history(user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    rows = list(db.scalars(select(TeacherAIMessage).where(TeacherAIMessage.teacher_id == user.id)
                           .order_by(TeacherAIMessage.created_at.desc()).limit(60)))
    return [ChatMessageOut(id=m.id, role=m.role, mode=m.task, content=m.content,
                           citations=json.loads(m.citations) if m.citations else [], created_at=aware(m.created_at))
            for m in reversed(rows)]


@router.delete("/history", status_code=204)
def clear_history(user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    db.execute(delete(TeacherAIMessage).where(TeacherAIMessage.teacher_id == user.id))
    db.commit()


@router.get("/documents/{document_id}/pages", response_model=list[DocPage])
def document_pages(document_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Văn bản từng trang (để giáo viên xem đúng trang được trích dẫn với tài liệu Word/Slide)."""
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    owned_class(db, user, d.class_id)
    return [DocPage(page_number=p.page_number, text=p.text)
            for p in db.scalars(select(DocumentPage).where(DocumentPage.document_id == d.id).order_by(DocumentPage.page_number))]


def _file_name(title: str) -> str:
    base = unicodedata.normalize("NFKD", title.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")[:80] or "Tong_hop"
    return f"{base}.md"


@router.post("/save", response_model=DocumentOut, status_code=201)
def save_as_document(body: SaveIn, bg: BackgroundTasks, user: CurrentUser = Depends(require_teacher),
                     db: Session = Depends(get_db)):
    """Lưu bản tổng hợp thành tài liệu của lớp: học sinh đọc được và AI của lớp dùng làm nguồn."""
    c = owned_class(db, user, body.class_id)
    name = _file_name(body.title)
    text = f"# {body.title.strip()}\n\n{body.content.strip()}\n"
    d = Document(class_id=c.id, file_name=name, file_key="", content_type="text/markdown")
    db.add(d)
    db.flush()
    d.file_key = storage.put_file(f"classes/{c.id}/documents/{d.id}.md", text.encode("utf-8"), "text/markdown")
    db.commit()
    enqueue_ingest(bg, d.id)
    return document_out(d)
