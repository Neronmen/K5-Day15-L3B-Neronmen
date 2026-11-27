"""API học sinh. Mọi route yêu cầu role=student và chỉ truy cập lớp mình đã tham gia."""
import json
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.chat import plan_chat, sse_stream
from app.core import storage
from app.core.config import settings
from app.core.security import CurrentUser, require_student
from app.db import get_db
from app.grading.image import is_blurry
from app.grading.service import mark_queued
from app.ingestion.pipeline import unit_label
from app.models import (
    Announcement, Assignment, ChatMessage, ClassMember, Classroom, DocStatus, Document, DocumentPage, Grade, GradeStatus, Submission, User,
)
from app.routers.common import (
    assignment_out, aware, class_out, document_out, enrolled_assignment, enrolled_class, my_submission,
    submission_out, utcnow,
)
from app.schedule import (
    announcement_out, calendar, class_sessions, next_sessions, schedule_text, session_out, today_vn,
)
from app.schemas import (
    AnnouncementOut, CalendarItem, ChatIn, ChatMessageOut, ClassOut, DocPage, DocumentOut, JoinIn, ResultOut, StudentAssignmentDetail,
    StudentAssignmentOut, StudentClassOut, StudentDocumentOut, StudentHome, SubmissionOut,
)
from app.tasks import enqueue_grade

router = APIRouter(prefix="/student", tags=["học sinh"])

IMG_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/heic": ".heic"}
MAX_IMG_BYTES = 10 * 1024 * 1024
MAX_TEXT = 50_000
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def _my_status(a: Assignment, s: Submission | None) -> str:
    if s:
        return "late" if s.is_late else "submitted"
    return "overdue" if aware(a.due_at) <= utcnow() else "missing"


@router.get("/home", response_model=StudentHome)
def student_home(user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    """Các lớp đã tham gia và bài tập (chưa nộp hoặc còn hạn), sắp xếp theo hạn."""
    rows = db.execute(
        select(Classroom, User.name).join(ClassMember, ClassMember.class_id == Classroom.id)
        .join(User, User.id == Classroom.teacher_id).where(ClassMember.student_id == user.id)
        .order_by(Classroom.name)
    ).all()
    upcoming_sessions = next_sessions(db, [c for c, _ in rows])
    classes = [StudentClassOut(**class_out(c).model_dump(), teacher_name=t, next_session_at=upcoming_sessions.get(c.id),
                               schedule_text=schedule_text(class_sessions(db, c.id))) for c, t in rows]
    names = {c.id: c.name for c, _ in rows}
    upcoming = []
    now = utcnow()
    for a in db.scalars(select(Assignment).where(Assignment.class_id.in_(names)).order_by(Assignment.due_at)):
        s = my_submission(db, a.id, user.id)
        if s and aware(a.due_at) <= now:
            continue
        upcoming.append(StudentAssignmentOut(**assignment_out(db, a, for_teacher=False).model_dump(),
                                             class_name=names[a.class_id], my_status=_my_status(a, s)))
    return StudentHome(classes=classes, upcoming=upcoming, announcements=_recent_announcements(db, names))


@router.post("/join", response_model=ClassOut)
def join_class(body: JoinIn, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    """Tham gia lớp bằng Class Code."""
    c = db.scalar(select(Classroom).where(Classroom.class_code == body.class_code.strip().upper()))
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mã lớp không đúng")
    if not db.get(ClassMember, (c.id, user.id)):
        db.add(ClassMember(class_id=c.id, student_id=user.id))
        db.commit()
    return class_out(c)


@router.get("/classes/{class_id}")
def class_view(class_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    c = enrolled_class(db, user, class_id)
    docs = db.scalars(select(Document).where(Document.class_id == c.id, Document.status == DocStatus.READY.value)
                      .order_by(Document.uploaded_at.desc()))
    asg = []
    for a in db.scalars(select(Assignment).where(Assignment.class_id == c.id).order_by(Assignment.due_at)):
        asg.append(StudentAssignmentOut(**assignment_out(db, a, for_teacher=False).model_dump(), class_name=c.name,
                                        my_status=_my_status(a, my_submission(db, a.id, user.id))))
    return {"cls": class_out(c), "documents": [document_out(d) for d in docs], "assignments": asg,
            "sessions": [session_out(s) for s in class_sessions(db, c.id)],
            "announcements": _recent_announcements(db, {c.id: c.name}, limit=100, days=None)}


@router.get("/classes/{class_id}/documents", response_model=list[DocumentOut])
def class_documents(class_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    c = enrolled_class(db, user, class_id)
    return [document_out(d) for d in db.scalars(
        select(Document).where(Document.class_id == c.id, Document.status == DocStatus.READY.value))]


# ---------- Bài giảng + Knowledge Agent ----------
def _ready_document(db: Session, user: CurrentUser, document_id: str) -> tuple[Document, Classroom]:
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    c = enrolled_class(db, user, d.class_id)
    if d.status != DocStatus.READY.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tài liệu chưa sẵn sàng")
    return d, c


@router.get("/documents/{document_id}", response_model=StudentDocumentOut)
def document_view(document_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    d, c = _ready_document(db, user, document_id)
    return StudentDocumentOut(id=d.id, class_id=c.id, class_name=c.name, ai_mode=c.ai_mode, file_name=d.file_name,
                              page_count=d.page_count, is_pdf=d.file_name.lower().endswith(".pdf"),
                              unit=unit_label(d.file_name))


@router.get("/documents/{document_id}/pages", response_model=list[DocPage])
def document_pages(document_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    d, _ = _ready_document(db, user, document_id)
    return [DocPage(page_number=p.page_number, text=p.text)
            for p in db.scalars(select(DocumentPage).where(DocumentPage.document_id == d.id).order_by(DocumentPage.page_number))]


def _history_out(rows) -> list[ChatMessageOut]:
    return [ChatMessageOut(id=m.id, role=m.role, mode=m.mode, content=m.content,
                           citations=json.loads(m.citations) if m.citations else [], created_at=aware(m.created_at))
            for m in rows]


@router.get("/documents/{document_id}/chat", response_model=list[ChatMessageOut])
def lecture_history(document_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    d, _ = _ready_document(db, user, document_id)
    return _history_out(db.scalars(select(ChatMessage).where(
        ChatMessage.student_id == user.id, ChatMessage.document_id == d.id, ChatMessage.assignment_id.is_(None)
    ).order_by(ChatMessage.created_at).limit(200)))


@router.post("/documents/{document_id}/chat")
def lecture_chat(document_id: str, req: ChatIn, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    """Knowledge Agent, stream SSE, trả lời kèm [Nguồn: Tên_file - Trang X]."""
    d, c = _ready_document(db, user, document_id)
    plan = plan_chat(db, student_id=user.id, cls=c, question=req.question, document=d)
    return StreamingResponse(sse_stream(plan), media_type="text/event-stream", headers=SSE_HEADERS)


# ---------- Bài tập ----------
@router.get("/assignments/{assignment_id}", response_model=StudentAssignmentDetail)
def assignment_view(assignment_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    """Đề bài (phiên bản hiện tại, không kèm đáp án mẫu) và bài nộp của em."""
    a = enrolled_assignment(db, user, assignment_id)
    s = my_submission(db, a.id, user.id)
    can = s is None and (a.allow_late or aware(a.due_at) > utcnow())
    return StudentAssignmentDetail(assignment=assignment_out(db, a, for_teacher=False),
                                   submission=submission_out(s) if s else None, can_submit=can)


@router.get("/assignments/{assignment_id}/chat", response_model=list[ChatMessageOut])
def tutor_history(assignment_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    a = enrolled_assignment(db, user, assignment_id)
    return _history_out(db.scalars(select(ChatMessage).where(
        ChatMessage.student_id == user.id, ChatMessage.assignment_id == a.id).order_by(ChatMessage.created_at).limit(200)))


@router.post("/assignments/{assignment_id}/chat")
def tutor_chat(assignment_id: str, req: ChatIn, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    """Trợ lý giải bài (is_assignment_context=True): Socratic Mode khi còn hạn, đáp án sau hạn (Rule 3)."""
    a = enrolled_assignment(db, user, assignment_id)
    c = db.get(Classroom, a.class_id)
    plan = plan_chat(db, student_id=user.id, cls=c, question=req.question, assignment=a)
    return StreamingResponse(sse_stream(plan), media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/assignments/{assignment_id}/submit", response_model=SubmissionOut, status_code=201)
async def submit(
    assignment_id: str,
    bg: BackgroundTasks,
    content: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    user: CurrentUser = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Nộp bài (text và/hoặc ảnh). Ảnh mờ → báo chụp lại ngay. Nộp xong khoá bài (Rule 5) → AI chấm nháp."""
    a = enrolled_assignment(db, user, assignment_id)
    if my_submission(db, a.id, user.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Em đã nộp bài này. Bài nộp đã khoá, không sửa được.")
    now = utcnow()
    late = now > aware(a.due_at)
    if late and not a.allow_late:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Đã hết hạn nộp")
    text = (content or "").strip() or None
    if text and len(text) > MAX_TEXT:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Bài làm quá dài")
    img_data = None
    if image is not None and image.filename:
        if image.content_type not in IMG_TYPES:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Ảnh cần là JPG, PNG, WEBP hoặc HEIC")
        img_data = await image.read()
        if len(img_data) > MAX_IMG_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Ảnh tối đa 10MB")
        if is_blurry(img_data):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "Ảnh bị mờ, AI và giáo viên khó đọc. Em chụp lại gần hơn, đủ sáng, giữ máy thẳng rồi nộp lại. Bài chưa được nộp.")
    if not text and not img_data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bài nộp cần có nội dung hoặc ảnh")

    s = Submission(assignment_id=a.id, assignment_version=a.current_version, student_id=user.id,
                   content=text, locked=True, submitted_at=now, is_late=late)
    db.add(s)
    try:
        db.flush()
    except IntegrityError:  # hai request nộp cùng lúc
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Em đã nộp bài này")
    if img_data:
        ext = IMG_TYPES[image.content_type]
        s.image_key = storage.put_file(f"classes/{a.class_id}/submissions/{s.id}{ext}", img_data, image.content_type)
    db.commit()
    if settings.auto_grade:
        mark_queued(db, s.id)
        enqueue_grade(bg, s.id)
    return submission_out(s)


@router.get("/assignments/{assignment_id}/result", response_model=ResultOut)
def result(assignment_id: str, user: CurrentUser = Depends(require_student), db: Session = Depends(get_db)):
    """Chỉ trả điểm khi giáo viên đã công bố (Rule 4). Không bao giờ trả điểm nháp AI."""
    a = enrolled_assignment(db, user, assignment_id)
    s = my_submission(db, a.id, user.id)
    if not s:
        return ResultOut(published=False)
    g = db.get(Grade, s.id)
    if not g or g.status != GradeStatus.PUBLISHED.value:
        return ResultOut(published=False, submission=submission_out(s))
    return ResultOut(published=True, score=g.score, feedback=g.feedback, breakdown=g.breakdown, submission=submission_out(s))


# ---------- Thông báo & lịch học ----------
def _recent_announcements(db: Session, names: dict[str, str], limit: int = 8, days: int | None = 30) -> list[AnnouncementOut]:
    """Thông báo của các lớp: ghim lên đầu, rồi mới nhất. Trang chủ chỉ lấy 30 ngày gần đây (luôn kèm tin ghim)."""
    if not names:
        return []
    stmt = select(Announcement).where(Announcement.class_id.in_(names))
    if days is not None:
        since = utcnow() - timedelta(days=days)
        stmt = stmt.where(Announcement.pinned.is_(True) | (Announcement.created_at >= since))
    rows = db.scalars(stmt.order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).limit(limit))
    return [announcement_out(a, names[a.class_id]) for a in rows]


@router.get("/calendar", response_model=list[CalendarItem])
def student_calendar(start: date | None = None, days: int = 7, user: CurrentUser = Depends(require_student),
                     db: Session = Depends(get_db)):
    """Lịch học của các lớp em tham gia, đã đánh dấu buổi nghỉ và buổi học bù."""
    classes = list(db.scalars(select(Classroom).join(ClassMember, ClassMember.class_id == Classroom.id)
                              .where(ClassMember.student_id == user.id)))
    return calendar(db, classes, start or today_vn(), days)
