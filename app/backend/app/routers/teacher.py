"""API giáo viên. Mọi route yêu cầu role=teacher; route theo lớp còn kiểm tra quyền sở hữu lớp."""
import csv
import io
import json
import re
import secrets
import unicodedata
from datetime import date
from pathlib import Path

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.security import CurrentUser, require_teacher
from app.db import get_db
from app.grading.service import mark_queued
from app.ingestion.pipeline import extract_pages
from app.models import (
    Announcement, AnnouncementKind, Assignment, AssignmentVersion, ChatMessage, ClassMember, ClassSession, Classroom,
    DocStatus, Document, DocumentPage, Grade, GradeStatus, LectureChunk, Notification, Role, Submission, User,
)
from app.schedule import (
    announcement_out, calendar, class_sessions, next_sessions, schedule_text, session_out, today_vn,
)
from app.routers.common import (
    assignment_out, aware, class_out, document_out, owned_assignment, owned_class, submission_out, utcnow,
)
from app.schemas import (
    AddStudentsIn, AddStudentsOut, AnnouncementIn, AnnouncementOut, AnnouncementPatch, AssignmentIn, CalendarItem,
    SessionIn, SessionOut, AssignmentOut, AssignmentUpdate, ChatLogOut, ClassDetail, ClassIn,
    ClassOut, ClassPatch, ClassSummary, DocumentOut, GradeDetail, MemberOut, PublishGradeIn, SubmissionOut,
    SubmissionStatusRow,
)
from app.tasks import enqueue_grade, enqueue_ingest

router = APIRouter(prefix="/teacher", tags=["giáo viên"])

DOC_EXT = {".pdf", ".docx", ".pptx"}
MAX_DOC_BYTES = 50 * 1024 * 1024
MAX_CSV_BYTES = 2 * 1024 * 1024
ATTACH_EXT = {".pdf", ".docx"}
MAX_ATTACH_BYTES = 20 * 1024 * 1024
MAX_ATTACH_TEXT = 20_000


def class_code(db: Session, name: str) -> str:
    base = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]", "", base).upper()[:6] or "LOP"
    while True:
        code = f"{base}-{secrets.token_hex(2).upper()[:3]}"
        if not db.scalar(select(Classroom.id).where(Classroom.class_code == code)):
            return code


# ---------- Lớp ----------
@router.get("/dashboard", response_model=list[ClassSummary])
def dashboard(user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Tổng quan các lớp đang dạy."""
    out = []
    now = utcnow()
    classes = list(db.scalars(select(Classroom).where(Classroom.teacher_id == user.id).order_by(Classroom.created_at)))
    upcoming = next_sessions(db, classes)
    for c in classes:
        students = db.scalar(select(func.count()).select_from(ClassMember).where(ClassMember.class_id == c.id))
        docs = db.scalar(select(func.count()).select_from(Document).where(Document.class_id == c.id))
        open_a = sum(1 for a in db.scalars(select(Assignment).where(Assignment.class_id == c.id)) if aware(a.due_at) > now)
        pending = db.scalar(
            select(func.count()).select_from(Submission)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .outerjoin(Grade, Grade.submission_id == Submission.id)
            .where(Assignment.class_id == c.id)
            .where((Grade.status.is_(None)) | (Grade.status == GradeStatus.PENDING_REVIEW.value))
        )
        out.append(ClassSummary(**class_out(c).model_dump(), students=students, documents=docs,
                                open_assignments=open_a, pending_grades=pending,
                                next_session_at=upcoming.get(c.id), schedule_text=schedule_text(class_sessions(db, c.id))))
    return out


@router.post("/classes", response_model=ClassOut, status_code=201)
def create_class(body: ClassIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Tạo lớp: tên, môn, ai_mode (strict | extended). Sinh class_code."""
    c = Classroom(teacher_id=user.id, name=body.name.strip(), subject_id=body.subject.strip(),
                  ai_mode=body.ai_mode, class_code=class_code(db, body.name))
    db.add(c)
    db.commit()
    return class_out(c)


@router.get("/classes/{class_id}", response_model=ClassDetail)
def class_detail(class_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    c = owned_class(db, user, class_id)
    members = db.scalars(
        select(User).join(ClassMember, ClassMember.student_id == User.id)
        .where(ClassMember.class_id == c.id).order_by(User.name)
    )
    docs = db.scalars(select(Document).where(Document.class_id == c.id).order_by(Document.uploaded_at.desc()))
    asg = db.scalars(select(Assignment).where(Assignment.class_id == c.id).order_by(Assignment.due_at))
    return ClassDetail(
        cls=class_out(c),
        members=[MemberOut(id=u.id, email=u.email, name=u.name, activated=bool(u.password_hash or u.google_sub)) for u in members],
        documents=[document_out(d) for d in docs],
        assignments=[assignment_out(db, a, for_teacher=True) for a in asg],
        sessions=[session_out(s) for s in class_sessions(db, c.id)],
        announcements=_class_announcements(db, c),
    )


@router.patch("/classes/{class_id}", response_model=ClassOut)
def update_class(class_id: str, body: ClassPatch, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    c = owned_class(db, user, class_id)
    if body.name is not None:
        c.name = body.name.strip()
    if body.ai_mode is not None:
        c.ai_mode = body.ai_mode
    db.commit()
    return class_out(c)


# ---------- Học sinh trong lớp ----------
def _add_students(db: Session, c: Classroom, rows: list[tuple[str, str | None]]) -> AddStudentsOut:
    added, already, invalid = [], [], []
    seen = set()
    for raw, name in rows:
        try:
            email = validate_email(raw.strip(), check_deliverability=False).normalized.lower()
        except EmailNotValidError:
            invalid.append(raw)
            continue
        if email in seen:
            continue
        seen.add(email)
        u = db.scalar(select(User).where(User.email == email))
        if u and u.role != Role.STUDENT.value:
            invalid.append(raw)  # không thêm tài khoản giáo viên vào lớp như học sinh
            continue
        if not u:
            u = User(email=email, name=(name or email.split("@")[0]).strip(), role=Role.STUDENT.value)
            db.add(u)
            db.flush()
        if db.get(ClassMember, (c.id, u.id)):
            already.append(email)
            continue
        db.add(ClassMember(class_id=c.id, student_id=u.id))
        added.append(email)
    db.commit()
    return AddStudentsOut(added=added, already_in_class=already, invalid=invalid)


@router.post("/classes/{class_id}/students", response_model=AddStudentsOut)
def add_students(class_id: str, body: AddStudentsIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Thêm học sinh bằng email. Email chưa có tài khoản → tạo tài khoản chờ kích hoạt."""
    c = owned_class(db, user, class_id)
    return _add_students(db, c, [(e, None) for e in body.emails if e.strip()])


@router.post("/classes/{class_id}/students/import", response_model=AddStudentsOut)
async def import_students(class_id: str, file: UploadFile, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Import danh sách học sinh từ CSV. Cần cột email; cột tên (name / họ tên) không bắt buộc."""
    c = owned_class(db, user, class_id)
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Chỉ nhận file .csv. Với Excel, chọn Lưu dưới dạng CSV UTF-8.")
    data = await file.read()
    if len(data) > MAX_CSV_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File CSV tối đa 2MB")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File cần mã hoá UTF-8")
    rows = [r for r in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in r)]
    if not rows:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File CSV trống")
    header = [h.strip().lower() for h in rows[0]]
    email_col = next((i for i, h in enumerate(header) if h in {"email", "e-mail", "mail"}), None)
    name_col = next((i for i, h in enumerate(header) if h in {"name", "họ tên", "ho ten", "họ và tên", "tên"}), None)
    if email_col is None:
        email_col = next((i for i, cell in enumerate(rows[0]) if "@" in cell), None)
        if email_col is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không tìm thấy cột email")
    else:
        rows = rows[1:]
    parsed = [(r[email_col], r[name_col] if name_col is not None and name_col < len(r) else None)
              for r in rows if email_col < len(r) and r[email_col].strip()]
    return _add_students(db, c, parsed)


@router.delete("/classes/{class_id}/students/{student_id}", status_code=204)
def remove_student(class_id: str, student_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    c = owned_class(db, user, class_id)
    m = db.get(ClassMember, (c.id, student_id))
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Học sinh không thuộc lớp này")
    db.delete(m)
    db.commit()


# ---------- Tài liệu ----------
@router.post("/classes/{class_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(class_id: str, file: UploadFile, bg: BackgroundTasks,
                          user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Upload PDF/Word/Slide → lưu file gốc → đẩy job bóc tách + chia đoạn vào hàng đợi."""
    c = owned_class(db, user, class_id)
    name = Path(file.filename or "").name
    ext = Path(name).suffix.lower()
    if ext in {".doc", ".ppt"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Định dạng {ext} cũ chưa đọc được. Hãy lưu lại thành .docx/.pptx hoặc PDF.")
    if ext not in DOC_EXT:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Chỉ nhận PDF, Word (.docx) hoặc Slide (.pptx)")
    data = await file.read()
    if len(data) > MAX_DOC_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Tài liệu tối đa 50MB")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File trống")
    d = Document(class_id=c.id, file_name=name, file_key="", content_type=file.content_type)
    db.add(d)
    db.flush()
    d.file_key = storage.put_file(f"classes/{c.id}/documents/{d.id}{ext}", data, file.content_type)
    db.commit()
    enqueue_ingest(bg, d.id)
    return document_out(d)


@router.get("/classes/{class_id}/documents", response_model=list[DocumentOut])
def list_documents(class_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    c = owned_class(db, user, class_id)
    return [document_out(d) for d in db.scalars(select(Document).where(Document.class_id == c.id).order_by(Document.uploaded_at.desc()))]


def _owned_document(db: Session, user: CurrentUser, document_id: str) -> Document:
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    owned_class(db, user, d.class_id)
    return d


@router.post("/documents/{document_id}/reprocess", response_model=DocumentOut)
def reprocess_document(document_id: str, bg: BackgroundTasks, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    d = _owned_document(db, user, document_id)
    d.status, d.error = DocStatus.PROCESSING.value, None
    db.commit()
    enqueue_ingest(bg, d.id)
    return document_out(d)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Xoá tài liệu: AI không còn dùng các đoạn của tài liệu này."""
    d = _owned_document(db, user, document_id)
    db.execute(delete(LectureChunk).where(LectureChunk.document_id == d.id))
    db.execute(delete(DocumentPage).where(DocumentPage.document_id == d.id))
    db.query(ChatMessage).filter(ChatMessage.document_id == d.id).update({ChatMessage.document_id: None})
    db.delete(d)
    db.commit()


# ---------- Bài tập ----------
@router.post("/classes/{class_id}/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(class_id: str, body: AssignmentIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Tạo bài tập có deadline + rubric. Đáp án mẫu chỉ đưa cho AI gia sư sau hạn."""
    c = owned_class(db, user, class_id)
    if body.due_at.tzinfo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "due_at cần kèm múi giờ, vd 2026-11-25T23:59:00+07:00")
    a = Assignment(class_id=c.id, due_at=body.due_at, allow_late=body.allow_late, source=body.source, current_version=1)
    db.add(a)
    db.flush()
    db.add(AssignmentVersion(assignment_id=a.id, version=1, title=body.title, prompt=body.prompt,
                             rubric=body.rubric, reference_answer=body.reference_answer))
    db.commit()
    return assignment_out(db, a, for_teacher=True)


@router.get("/assignments/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    return assignment_out(db, owned_assignment(db, user, assignment_id), for_teacher=True)


@router.put("/assignments/{assignment_id}", response_model=AssignmentOut)
def update_assignment(assignment_id: str, body: AssignmentUpdate, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Rule 5: sửa đề tạo phiên bản mới, bài đã nộp giữ phiên bản cũ."""
    a = owned_assignment(db, user, assignment_id)
    if body.due_at is not None and body.due_at.tzinfo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "due_at cần kèm múi giờ")
    a.current_version += 1
    db.add(AssignmentVersion(assignment_id=a.id, version=a.current_version, title=body.title, prompt=body.prompt,
                             rubric=body.rubric, reference_answer=body.reference_answer))
    if body.due_at is not None:
        a.due_at = body.due_at
    if body.allow_late is not None:
        a.allow_late = body.allow_late
    db.commit()
    return assignment_out(db, a, for_teacher=True)


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionStatusRow])
def submission_status(assignment_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Trạng thái nộp bài: Đã nộp / Chưa nộp / Nộp muộn, kèm trạng thái AI chấm nháp và điểm."""
    a = owned_assignment(db, user, assignment_id)
    subs = {s.student_id: s for s in db.scalars(select(Submission).where(Submission.assignment_id == a.id))}
    grades = {g.submission_id: g for g in db.scalars(select(Grade).where(Grade.submission_id.in_([s.id for s in subs.values()])))}
    students = db.scalars(
        select(User).join(ClassMember, ClassMember.student_id == User.id).where(ClassMember.class_id == a.class_id).order_by(User.name)
    )
    rows = []
    for u in students:
        s = subs.get(u.id)
        g = grades.get(s.id) if s else None
        rows.append(SubmissionStatusRow(
            student_id=u.id, name=u.name, email=u.email,
            status="missing" if not s else ("late" if s.is_late else "submitted"),
            submitted_at=aware(s.submitted_at) if s else None, submission_id=s.id if s else None,
            grade_status=g.status if g else None, score=g.score if g else None,
            ai_status=g.ai_status if g else None, ai_score=g.ai_score if g else None,
        ))
    return rows


def _owned_submission(db: Session, user: CurrentUser, submission_id: str) -> Submission:
    s = db.get(Submission, submission_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bài nộp")
    owned_assignment(db, user, s.assignment_id)
    return s


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(submission_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    return submission_out(_owned_submission(db, user, submission_id))


def _loads(s: str | None):
    try:
        return json.loads(s) if s else None
    except json.JSONDecodeError:
        return None


@router.get("/submissions/{submission_id}/grade", response_model=GradeDetail)
def grade_detail(submission_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Điểm nháp AI (OCR, các bước, kiểm tra logic, điểm rubric) + điểm chính thức nếu đã có."""
    s = _owned_submission(db, user, submission_id)
    g = db.get(Grade, s.id)
    if not g:
        return GradeDetail(submission_id=s.id, status=GradeStatus.PENDING_REVIEW.value, ai_status=None, ai_score=None,
                           ai_breakdown=None, ai_error=None, score=None, feedback=None, breakdown=None)
    return GradeDetail(submission_id=s.id, status=g.status, ai_status=g.ai_status, ai_score=g.ai_score,
                       ai_breakdown=_loads(g.ai_breakdown), ai_error=g.ai_error, score=g.score,
                       feedback=g.feedback, breakdown=_loads(g.breakdown))


@router.post("/submissions/{submission_id}/regrade", response_model=GradeDetail)
def regrade(submission_id: str, bg: BackgroundTasks, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    s = _owned_submission(db, user, submission_id)
    g = db.get(Grade, s.id)
    if g and g.status == GradeStatus.PUBLISHED.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Điểm đã công bố, không chấm lại bằng AI")
    mark_queued(db, s.id)
    enqueue_grade(bg, s.id)
    return grade_detail(submission_id, user, db)


@router.post("/grades/{submission_id}/publish")
def publish_grade(submission_id: str, body: PublishGradeIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Giáo viên sửa điểm/nhận xét (nếu cần) rồi Duyệt & Công bố (Rule 4)."""
    s = _owned_submission(db, user, submission_id)
    if body.breakdown is not None and not isinstance(_loads(body.breakdown), list):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "breakdown cần là JSON dạng danh sách")
    g = db.get(Grade, s.id) or Grade(submission_id=s.id)
    g.score = body.score
    g.feedback = body.feedback
    g.breakdown = body.breakdown
    g.status = GradeStatus.PUBLISHED.value
    g.reviewed_by = user.id
    db.merge(g)
    db.commit()
    return {"ok": True, "status": g.status}


@router.get("/classes/{class_id}/chats", response_model=list[ChatLogOut])
def chat_logs(class_id: str, flagged_only: bool = False, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Xem lại lịch sử hỏi AI của học sinh (chống gian lận)."""
    c = owned_class(db, user, class_id)
    stmt = (select(ChatMessage, User.name).join(User, User.id == ChatMessage.student_id)
            .where(ChatMessage.class_id == c.id))
    if flagged_only:
        stmt = stmt.where(ChatMessage.flagged.is_not(None))
    rows = db.execute(stmt.order_by(ChatMessage.created_at.desc()).limit(500)).all()
    docs = {d.id: d.file_name for d in db.scalars(select(Document).where(Document.class_id == c.id))}
    titles = {}
    for a in db.scalars(select(Assignment).where(Assignment.class_id == c.id)):
        titles[a.id] = db.get(AssignmentVersion, (a.id, a.current_version)).title
    return [ChatLogOut(
        id=m.id, role=m.role, mode=m.mode, content=m.content, citations=_loads(m.citations) or [],
        created_at=aware(m.created_at), student_id=m.student_id, student_name=name, flagged=m.flagged,
        assignment_id=m.assignment_id, document_id=m.document_id,
        context=titles.get(m.assignment_id) if m.assignment_id else docs.get(m.document_id, "Tài liệu đã xoá"),
    ) for m, name in rows]


# ---------- File đề bài tập ----------
@router.post("/assignments/{assignment_id}/attachment", response_model=AssignmentOut)
async def upload_attachment(assignment_id: str, file: UploadFile, user: CurrentUser = Depends(require_teacher),
                            db: Session = Depends(get_db)):
    """Đính kèm file đề (PDF/Word). Chữ trong file được đưa cho AI gia sư và AI chấm cùng với đề gõ tay."""
    a = owned_assignment(db, user, assignment_id)
    name = Path(file.filename or "").name
    ext = Path(name).suffix.lower()
    if ext == ".doc":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File .doc cũ chưa đọc được. Hãy lưu lại thành .docx hoặc PDF.")
    if ext not in ATTACH_EXT:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File đề chỉ nhận PDF hoặc Word (.docx)")
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File trống")
    if len(data) > MAX_ATTACH_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File đề tối đa 20MB")
    try:
        text = "\n\n".join(p.text for p in extract_pages(data, name)).strip()
    except Exception:  # noqa: BLE001 - file hỏng / PDF scan ảnh: vẫn lưu cho học sinh tải, AI không đọc được chữ
        text = ""
    a.attachment_key = storage.put_file(f"classes/{a.class_id}/assignments/{a.id}/de{ext}", data, file.content_type)
    a.attachment_name = name
    a.attachment_text = text[:MAX_ATTACH_TEXT] or None
    if a.source == "manual":
        a.source = "file"
    db.commit()
    return assignment_out(db, a, for_teacher=True)


@router.delete("/assignments/{assignment_id}/attachment", response_model=AssignmentOut)
def delete_attachment(assignment_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    a = owned_assignment(db, user, assignment_id)
    a.attachment_key = a.attachment_name = a.attachment_text = None
    db.commit()
    return assignment_out(db, a, for_teacher=True)


# ---------- Lịch học ----------
@router.get("/calendar", response_model=list[CalendarItem])
def teacher_calendar(start: date | None = None, days: int = 7, user: CurrentUser = Depends(require_teacher),
                     db: Session = Depends(get_db)):
    """Lịch dạy của tất cả các lớp, mặc định 7 ngày từ hôm nay."""
    classes = list(db.scalars(select(Classroom).where(Classroom.teacher_id == user.id)))
    return calendar(db, classes, start or today_vn(), days)


@router.post("/classes/{class_id}/sessions", response_model=SessionOut, status_code=201)
def add_session(class_id: str, body: SessionIn, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Thêm buổi học hằng tuần, vd Thứ 3 18:00–19:30. Chặn trùng giờ với lớp khác của cùng giáo viên."""
    c = owned_class(db, user, class_id)
    clash = db.execute(
        select(ClassSession, Classroom.name).join(Classroom, Classroom.id == ClassSession.class_id)
        .where(Classroom.teacher_id == user.id, ClassSession.weekday == body.weekday,
               ClassSession.start_time < body.end_time, ClassSession.end_time > body.start_time)
    ).first()
    if clash:
        s, name = clash
        raise HTTPException(status.HTTP_409_CONFLICT, f"Trùng giờ với lớp {name} ({s.start_time}–{s.end_time})")
    s = ClassSession(class_id=c.id, weekday=body.weekday, start_time=body.start_time, end_time=body.end_time,
                     room=(body.room or "").strip() or None)
    db.add(s)
    db.commit()
    return session_out(s)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    s = db.get(ClassSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy buổi học")
    owned_class(db, user, s.class_id)
    db.query(Announcement).filter(Announcement.session_id == s.id).update({Announcement.session_id: None})
    db.delete(s)
    db.commit()


# ---------- Thông báo lớp ----------
def _class_announcements(db: Session, c: Classroom) -> list[AnnouncementOut]:
    rows = db.scalars(select(Announcement).where(Announcement.class_id == c.id)
                      .order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).limit(100))
    return [announcement_out(a, c.name) for a in rows]


def _owned_announcement(db: Session, user: CurrentUser, announcement_id: str) -> tuple[Announcement, Classroom]:
    a = db.get(Announcement, announcement_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thông báo")
    return a, owned_class(db, user, a.class_id)


@router.get("/classes/{class_id}/announcements", response_model=list[AnnouncementOut])
def list_announcements(class_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    return _class_announcements(db, owned_class(db, user, class_id))


@router.post("/classes/{class_id}/announcements", response_model=AnnouncementOut, status_code=201)
def create_announcement(class_id: str, body: AnnouncementIn, user: CurrentUser = Depends(require_teacher),
                        db: Session = Depends(get_db)):
    """Đăng thông báo cho lớp (thường / báo nghỉ / học bù) và gửi thông báo tới từng học sinh."""
    c = owned_class(db, user, class_id)
    session_id = None
    if body.kind == AnnouncementKind.CANCEL.value and body.session_id:
        s = db.get(ClassSession, body.session_id)
        if not s or s.class_id != c.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Buổi học không thuộc lớp này")
        if s.weekday != body.event_date.weekday():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ngày nghỉ không rơi vào thứ của buổi học đã chọn")
        session_id = s.id
    is_makeup = body.kind == AnnouncementKind.MAKEUP.value
    a = Announcement(
        class_id=c.id, author_id=user.id, kind=body.kind, title=body.title.strip(), body=body.body.strip(),
        event_date=body.event_date if body.kind != AnnouncementKind.GENERAL.value else None,
        event_start=body.event_start if is_makeup else None, event_end=body.event_end if is_makeup else None,
        session_id=session_id, pinned=body.pinned,
    )
    db.add(a)
    db.flush()
    payload = json.dumps({"announcement_id": a.id, "class_id": c.id, "class_name": c.name, "title": a.title,
                          "kind": a.kind, "event_date": a.event_date.isoformat() if a.event_date else None},
                         ensure_ascii=False)
    for sid in db.scalars(select(ClassMember.student_id).where(ClassMember.class_id == c.id)):
        db.add(Notification(user_id=sid, kind="announcement", payload=payload))
    db.commit()
    return announcement_out(a, c.name)


@router.patch("/announcements/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(announcement_id: str, body: AnnouncementPatch, user: CurrentUser = Depends(require_teacher),
                        db: Session = Depends(get_db)):
    a, c = _owned_announcement(db, user, announcement_id)
    if body.title is not None:
        a.title = body.title.strip()
    if body.body is not None:
        a.body = body.body.strip()
    if body.pinned is not None:
        a.pinned = body.pinned
    db.commit()
    return announcement_out(a, c.name)


@router.delete("/announcements/{announcement_id}", status_code=204)
def delete_announcement(announcement_id: str, user: CurrentUser = Depends(require_teacher), db: Session = Depends(get_db)):
    """Xoá thông báo; nếu là báo nghỉ thì buổi học hiện lại bình thường trên lịch."""
    a, _ = _owned_announcement(db, user, announcement_id)
    db.delete(a)
    db.commit()
