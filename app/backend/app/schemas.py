from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

RoleT = Literal["teacher", "student"]
AIModeT = Literal["strict", "extended"]


# ---------- Auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    role: RoleT


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginIn(BaseModel):
    credential: str = Field(min_length=20)
    role: RoleT | None = None  # bắt buộc khi tạo tài khoản mới (từ trang Đăng ký)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Lớp ----------
class ClassIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    subject: str = Field(min_length=1, max_length=60)
    ai_mode: AIModeT = "strict"


class ClassPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    ai_mode: AIModeT | None = None


class ClassOut(BaseModel):
    id: str
    name: str
    subject: str
    ai_mode: str
    class_code: str


class ClassSummary(ClassOut):
    students: int
    documents: int
    open_assignments: int
    pending_grades: int
    next_session_at: datetime | None = None  # buổi học sắp tới (đã trừ buổi nghỉ)
    schedule_text: str = ""  # vd "T2 18:00–19:30 · T5 18:00–19:30"


class AddStudentsIn(BaseModel):
    emails: list[str] = Field(min_length=1, max_length=500)


class AddStudentsOut(BaseModel):
    added: list[str]
    already_in_class: list[str]
    invalid: list[str]


class MemberOut(BaseModel):
    id: str
    email: str
    name: str
    activated: bool  # False = được mời, chưa đặt mật khẩu


class DocumentOut(BaseModel):
    id: str
    file_name: str
    status: str
    uploaded_at: datetime | None
    page_count: int | None = None
    error: str | None = None
    is_pdf: bool = False


# ---------- Bài tập ----------
class AssignmentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    due_at: datetime
    rubric: str | None = None
    reference_answer: str | None = None
    allow_late: bool = True
    source: Literal["manual", "file", "ai_generated"] = "manual"


class AssignmentUpdate(BaseModel):
    """Sửa đề → tạo phiên bản mới (Rule 5)."""
    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    rubric: str | None = None
    reference_answer: str | None = None
    due_at: datetime | None = None
    allow_late: bool | None = None


class AssignmentOut(BaseModel):
    id: str
    class_id: str
    title: str
    prompt: str
    rubric: str | None
    due_at: datetime
    allow_late: bool
    version: int
    reference_answer: str | None = None  # chỉ trả cho giáo viên
    attachment_name: str | None = None  # file đề đính kèm, tải qua /files/assignments/{id}/attachment


class ClassDetail(BaseModel):
    cls: ClassOut
    members: list[MemberOut]
    documents: list[DocumentOut]
    assignments: list[AssignmentOut]
    sessions: list["SessionOut"] = []
    announcements: list["AnnouncementOut"] = []


class SubmissionOut(BaseModel):
    id: str
    assignment_version: int
    content: str | None
    has_image: bool
    locked: bool
    submitted_at: datetime | None
    is_late: bool


class SubmissionStatusRow(BaseModel):
    student_id: str
    name: str
    email: str
    status: Literal["submitted", "late", "missing"]
    submitted_at: datetime | None
    submission_id: str | None
    grade_status: str | None
    score: float | None
    ai_status: str | None = None
    ai_score: float | None = None


class PublishGradeIn(BaseModel):
    score: float = Field(ge=0, le=10)
    feedback: str | None = None
    breakdown: str | None = None  # JSON các tiêu chí rubric công bố cho học sinh


class GradeDetail(BaseModel):
    submission_id: str
    status: str
    ai_status: str | None
    ai_score: float | None
    ai_breakdown: dict | None
    ai_error: str | None
    score: float | None
    feedback: str | None
    breakdown: list | None


class ResultOut(BaseModel):
    published: bool
    score: float | None = None
    feedback: str | None = None
    breakdown: str | None = None
    submission: SubmissionOut | None = None


class JoinIn(BaseModel):
    class_code: str = Field(min_length=3, max_length=40)


class StudentAssignmentOut(AssignmentOut):
    class_name: str
    my_status: Literal["missing", "submitted", "late", "overdue"]


class StudentAssignmentDetail(BaseModel):
    assignment: AssignmentOut
    submission: SubmissionOut | None
    can_submit: bool


class StudentClassOut(ClassOut):
    teacher_name: str
    next_session_at: datetime | None = None
    schedule_text: str = ""


class StudentHome(BaseModel):
    classes: list[StudentClassOut]
    upcoming: list[StudentAssignmentOut]
    announcements: list["AnnouncementOut"] = []


class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class ChatMessageOut(BaseModel):
    id: str
    role: str
    mode: str
    content: str
    citations: list = []
    created_at: datetime | None


class ChatLogOut(ChatMessageOut):
    student_id: str
    student_name: str
    flagged: str | None
    assignment_id: str | None
    document_id: str | None
    context: str  # tên tài liệu hoặc bài tập


class DocPage(BaseModel):
    page_number: int
    text: str


class StudentDocumentOut(BaseModel):
    id: str
    class_id: str
    class_name: str
    ai_mode: str
    file_name: str
    page_count: int | None
    is_pdf: bool
    unit: str  # Trang | Slide | Phần


class NotificationOut(BaseModel):
    id: str
    kind: str
    payload: dict
    read: bool
    created_at: datetime | None


# ---------- Lịch học & thông báo ----------
_HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"


class SessionIn(BaseModel):
    weekday: int = Field(ge=0, le=6)  # 0 = Thứ 2 … 6 = Chủ nhật
    start_time: str = Field(pattern=_HHMM)
    end_time: str = Field(pattern=_HHMM)
    room: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _order(self):
        if self.end_time <= self.start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        return self


class SessionOut(BaseModel):
    id: str
    weekday: int
    start_time: str
    end_time: str
    room: str | None


AnnouncementKindT = Literal["general", "cancel", "makeup"]


class AnnouncementIn(BaseModel):
    kind: AnnouncementKindT = "general"
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=5000)
    event_date: date | None = None
    event_start: str | None = Field(default=None, pattern=_HHMM)
    event_end: str | None = Field(default=None, pattern=_HHMM)
    session_id: str | None = None  # báo nghỉ một buổi cụ thể; bỏ trống = nghỉ cả ngày
    pinned: bool = False

    @model_validator(mode="after")
    def _check(self):
        if self.kind in ("cancel", "makeup") and self.event_date is None:
            raise ValueError("Cần chọn ngày nghỉ / ngày học bù")
        if self.kind == "makeup":
            if not (self.event_start and self.event_end):
                raise ValueError("Buổi học bù cần giờ bắt đầu và kết thúc")
            if self.event_end <= self.event_start:
                raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        return self


class AnnouncementPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=5000)
    pinned: bool | None = None


class AnnouncementOut(BaseModel):
    id: str
    class_id: str
    class_name: str
    kind: str
    title: str
    body: str
    event_date: date | None
    event_start: str | None
    event_end: str | None
    session_id: str | None
    pinned: bool
    created_at: datetime | None


class CalendarItem(BaseModel):
    date: date
    start_time: str
    end_time: str
    class_id: str
    class_name: str
    subject: str
    room: str | None
    kind: Literal["regular", "makeup"]
    session_id: str | None
    cancelled: bool = False
    note: str | None = None  # tiêu đề thông báo nghỉ / học bù


ClassDetail.model_rebuild()
StudentHome.model_rebuild()
