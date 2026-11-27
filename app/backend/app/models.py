import uuid
from datetime import date, datetime, timezone
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Role(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    # None = tài khoản do giáo viên mời, học sinh chưa đặt mật khẩu (đăng ký bằng đúng email này để kích hoạt)
    password_hash: Mapped[str | None] = mapped_column(String)
    google_sub: Mapped[str | None] = mapped_column(String, unique=True)  # ID tài khoản Google đã liên kết
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIMode(str, Enum):
    STRICT = "strict"      # Khoá cứng theo bài giảng
    EXTENDED = "extended"  # Mở rộng, bắt buộc trích nguồn ngoài


class Classroom(Base):
    __tablename__ = "classes"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String)  # vd "Toán"
    name: Mapped[str] = mapped_column(String)  # vd "Toán 10A1 - Học kỳ 1"
    ai_mode: Mapped[str] = mapped_column(String, default=AIMode.STRICT.value)
    class_code: Mapped[str] = mapped_column(String, unique=True, index=True)  # mã mời học sinh
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClassMember(Base):
    __tablename__ = "class_members"
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"      # đã sẵn sàng cho AI → thông báo giáo viên
    FAILED = "failed"


class Document(Base):
    """File bài giảng giáo viên upload (PDF/Word/Slide)."""
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    file_name: Mapped[str] = mapped_column(String)
    file_key: Mapped[str] = mapped_column(String)  # khoá trong object storage
    content_type: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default=DocStatus.PROCESSING.value)
    page_count: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)  # lý do xử lý lỗi, hiện cho giáo viên
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentPage(Base):
    """Văn bản từng trang sau khi bóc tách: để trình đọc hiển thị & nhảy đúng trang được trích dẫn."""
    __tablename__ = "document_pages"
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), primary_key=True)
    page_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)


class LectureChunk(Base):
    """Đoạn bài giảng đã vector hoá, luôn mang đủ 3 khoá tenant (Rule 2)."""
    __tablename__ = "lecture_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[int] = mapped_column(Integer)  # để thẻ nguồn nhảy đúng trang
    teacher_id: Mapped[str] = mapped_column(String, index=True)
    class_id: Mapped[str] = mapped_column(String, index=True)
    subject_id: Mapped[str] = mapped_column(String, index=True)
    source_label: Mapped[str] = mapped_column(String)  # vd "Dao_ham.pdf - Trang 12"
    text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1024), nullable=True)  # None khi chỉ dùng tìm theo từ khoá


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    allow_late: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_publish_mcq: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String, default="manual")  # manual | file | ai_generated
    # File đề giáo viên đính kèm (PDF/Word); chữ bóc ra được đưa cho AI gia sư và AI chấm
    attachment_key: Mapped[str | None] = mapped_column(String)
    attachment_name: Mapped[str | None] = mapped_column(String)
    attachment_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def full_prompt(self, prompt: str) -> str:
        """Đề bài gõ tay + nội dung file đề đính kèm (nếu có)."""
        if not self.attachment_text:
            return prompt
        return f"{prompt}\n\n[Đề trong file đính kèm {self.attachment_name}]\n{self.attachment_text}"


class AssignmentVersion(Base):
    """Rule 5: sửa đề sau khi giao tạo phiên bản mới, không ghi đè."""
    __tablename__ = "assignment_versions"
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    prompt: Mapped[str] = mapped_column(Text)
    rubric: Mapped[str | None] = mapped_column(Text)
    reference_answer: Mapped[str | None] = mapped_column(Text)  # chỉ đưa cho AI sau deadline
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"), index=True)
    assignment_version: Mapped[int] = mapped_column(Integer)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str | None] = mapped_column(Text)
    image_key: Mapped[str | None] = mapped_column(String)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)  # Rule 5: nộp/hết hạn → read-only
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    # Trạng thái hiển thị cho giáo viên: không có bản ghi = Chưa nộp; is_late = Nộp muộn; còn lại = Đã nộp


class GradeStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"


class AIGradeStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    MANUAL = "manual"   # không chấm tự động được (vd chưa cấu hình VLM) → giáo viên chấm tay
    FAILED = "failed"


class Grade(Base):
    """Rule 4: điểm AI chấm luôn bắt đầu ở pending_review; chỉ giáo viên công bố."""
    __tablename__ = "grades"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), primary_key=True)
    # Bản nháp AI (giáo viên xem, học sinh không thấy)
    ai_status: Mapped[str | None] = mapped_column(String)
    ai_score: Mapped[float | None]
    ai_breakdown: Mapped[str | None] = mapped_column(Text)  # JSON: OCR, các bước, kiểm tra logic, điểm rubric
    ai_error: Mapped[str | None] = mapped_column(Text)
    # Điểm chính thức do giáo viên duyệt
    score: Mapped[float | None]
    breakdown: Mapped[str | None] = mapped_column(Text)  # JSON điểm thành phần công bố cho học sinh
    feedback: Mapped[str | None] = mapped_column(Text)  # nhận xét giáo viên gửi học sinh
    status: Mapped[str] = mapped_column(String, default=GradeStatus.PENDING_REVIEW.value)
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String)  # doc_ready | new_assignment | grade_published | retake_photo
    payload: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    """Lưu toàn bộ hội thoại để giáo viên xem lại (chống gian lận)."""
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"))
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"))  # chat bên bài giảng
    assignment_id: Mapped[str | None] = mapped_column(ForeignKey("assignments.id"))  # chat gia sư bài tập
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String)  # user | assistant
    mode: Mapped[str] = mapped_column(String)  # hint | answer | lecture
    content: Mapped[str] = mapped_column(Text)
    flagged: Mapped[str | None] = mapped_column(String)  # vd "jailbreak", "ask_answer" để giáo viên xem lại
    citations: Mapped[str | None] = mapped_column(Text)  # JSON các thẻ nguồn hợp lệ của câu trả lời
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClassSession(Base):
    """Buổi học lặp lại hằng tuần của lớp, theo giờ Việt Nam (UTC+7)."""
    __tablename__ = "class_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Thứ 2 … 6 = Chủ nhật
    start_time: Mapped[str] = mapped_column(String)  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String)
    room: Mapped[str | None] = mapped_column(String)  # phòng học hoặc link học online
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnnouncementKind(str, Enum):
    GENERAL = "general"  # thông báo thường
    CANCEL = "cancel"    # báo nghỉ học một ngày (một buổi hoặc cả ngày)
    MAKEUP = "makeup"    # báo học bù: thêm buổi vào lịch


class Announcement(Base):
    """Thông báo của giáo viên cho một lớp; báo nghỉ / học bù được phản ánh trên lịch học."""
    __tablename__ = "announcements"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String, default=AnnouncementKind.GENERAL.value)
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text, default="")
    event_date: Mapped[date | None] = mapped_column(Date, index=True)  # ngày nghỉ / ngày học bù
    event_start: Mapped[str | None] = mapped_column(String)  # giờ học bù "HH:MM"
    event_end: Mapped[str | None] = mapped_column(String)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("class_sessions.id"))  # None = nghỉ cả ngày
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeacherAIMessage(Base):
    """Hội thoại của giáo viên với Trợ lý AI (tìm kiếm & tổng hợp tài liệu của chính mình)."""
    __tablename__ = "teacher_ai_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # user | assistant
    task: Mapped[str] = mapped_column(String, default="ask")  # ask | summary | outline | quiz | lesson
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[str | None] = mapped_column(Text)
    # Giờ ghi từ Python (có micro giây) để thứ tự hội thoại đúng cả trên SQLite
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 default=lambda: datetime.now(timezone.utc))
