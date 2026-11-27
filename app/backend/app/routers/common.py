"""Hàm dùng chung: tải tài nguyên kèm kiểm tra quyền (Rule 2: không lộ dữ liệu giữa các lớp)."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, assert_class_owner, assert_enrolled
from app.models import Assignment, AssignmentVersion, ClassMember, Classroom, Document, Submission
from app.schemas import AssignmentOut, ClassOut, DocumentOut, SubmissionOut


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt: datetime | None) -> datetime | None:
    """SQLite trả datetime không múi giờ: coi là UTC."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_class_or_404(db: Session, class_id: str) -> Classroom:
    c = db.get(Classroom, class_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lớp")
    return c


def owned_class(db: Session, user: CurrentUser, class_id: str) -> Classroom:
    c = get_class_or_404(db, class_id)
    assert_class_owner(user, c.teacher_id)
    return c


def is_member(db: Session, class_id: str, student_id: str) -> bool:
    return db.get(ClassMember, (class_id, student_id)) is not None


def enrolled_class(db: Session, user: CurrentUser, class_id: str) -> Classroom:
    c = get_class_or_404(db, class_id)
    assert_enrolled(is_member(db, class_id, user.id))
    return c


def get_assignment_or_404(db: Session, assignment_id: str) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bài tập")
    return a


def owned_assignment(db: Session, user: CurrentUser, assignment_id: str) -> Assignment:
    a = get_assignment_or_404(db, assignment_id)
    owned_class(db, user, a.class_id)
    return a


def enrolled_assignment(db: Session, user: CurrentUser, assignment_id: str) -> Assignment:
    a = get_assignment_or_404(db, assignment_id)
    enrolled_class(db, user, a.class_id)
    return a


def current_version(db: Session, a: Assignment) -> AssignmentVersion:
    return db.get(AssignmentVersion, (a.id, a.current_version))


def class_out(c: Classroom) -> ClassOut:
    return ClassOut(id=c.id, name=c.name, subject=c.subject_id, ai_mode=c.ai_mode, class_code=c.class_code)


def document_out(d: Document) -> DocumentOut:
    return DocumentOut(id=d.id, file_name=d.file_name, status=d.status, uploaded_at=aware(d.uploaded_at),
                       page_count=d.page_count, error=d.error, is_pdf=d.file_name.lower().endswith(".pdf"))


def assignment_out(db: Session, a: Assignment, for_teacher: bool) -> AssignmentOut:
    v = current_version(db, a)
    return AssignmentOut(
        id=a.id, class_id=a.class_id, title=v.title, prompt=v.prompt, rubric=v.rubric,
        due_at=aware(a.due_at), allow_late=a.allow_late, version=a.current_version,
        reference_answer=v.reference_answer if for_teacher else None, attachment_name=a.attachment_name,
    )


def submission_out(s: Submission) -> SubmissionOut:
    return SubmissionOut(
        id=s.id, assignment_version=s.assignment_version, content=s.content, has_image=bool(s.image_key),
        locked=s.locked, submitted_at=aware(s.submitted_at), is_late=s.is_late,
    )


def my_submission(db: Session, assignment_id: str, student_id: str) -> Submission | None:
    return db.scalar(
        select(Submission).where(Submission.assignment_id == assignment_id, Submission.student_id == student_id)
    )
