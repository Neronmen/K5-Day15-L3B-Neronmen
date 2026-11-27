"""N-08: nạp lớp mẫu Toán 10 (10A1) từ data/ của lõi vào DB của app, để demo đúng dữ liệu đã đo.

Chạy (trong app/backend, DB local SQLite):
    python scripts/seed_toan10.py
Tạo (chạy lại thì bỏ qua cái đã có):
    - tài khoản DEMO giáo viên + học sinh bên dưới (mật khẩu thử, chỉ dùng trên máy)
    - lớp "Toán 10A1 — Phương trình bậc hai (mẫu)", học sinh đã vào lớp
    - tài liệu bài giảng từ data/lesson.json (mỗi trang của lõi = một trang tài liệu, đúng số trang)
    - các bài tập của lớp 10A1 trong data/assignments.json (đề, hạn, đáp án mẫu = answer_key)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core import storage  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.ingestion.pipeline import extract_pages, save_pages_and_chunks  # noqa: E402
from app.models import (AIMode, Assignment, AssignmentVersion, Base, ClassMember, Classroom, DocStatus,  # noqa: E402
                        Document, User)

DATA = Path(__file__).resolve().parents[3] / "data"
CORE_CLASS = "10A1"
CLASS_NAME = "Toán 10A1 — Phương trình bậc hai (mẫu)"
DOC_NAME = "Chuong3_Phuong_trinh_bac_hai.md"
# Tên miền .local / .test bị EmailStr từ chối khi đăng nhập, nên dùng tên miền dạng thường như test của app.
TEACHER = {"email": "giaovien.demo@lopmau.vn", "name": "Cô Lan (demo)", "role": "teacher"}
STUDENT = {"email": "hocsinh.demo@lopmau.vn", "name": "Minh (demo)", "role": "student"}
DEMO_PASSWORD = "demo-toan10"   # mật khẩu thử cho 2 tài khoản demo trên máy, không dùng ở môi trường thật


def _user(db, info):
    u = db.scalar(select(User).where(User.email == info["email"]))
    if u is None:
        u = User(**info, password_hash=hash_password(DEMO_PASSWORD))
        db.add(u)
        db.flush()
    return u


def main() -> int:
    Base.metadata.create_all(engine)
    lesson = [p for p in json.loads((DATA / "lesson.json").read_text("utf-8")) if p["class_id"] == CORE_CLASS]
    tasks = [a for a in json.loads((DATA / "assignments.json").read_text("utf-8")) if a["class_id"] == CORE_CLASS]
    lesson.sort(key=lambda p: p["page"])
    if [p["page"] for p in lesson] != list(range(1, len(lesson) + 1)):
        print("data/lesson.json: số trang lớp %s không liên tục 1..n — dừng để thẻ nguồn không lệch trang" % CORE_CLASS)
        return 1

    db = SessionLocal()
    try:
        teacher, student = _user(db, TEACHER), _user(db, STUDENT)
        c = db.scalar(select(Classroom).where(Classroom.teacher_id == teacher.id, Classroom.name == CLASS_NAME))
        if c is not None:
            print("Đã có lớp mẫu (mã lớp %s) — không nạp lại." % c.class_code)
            return 0
        from app.routers.teacher import class_code

        c = Classroom(teacher_id=teacher.id, name=CLASS_NAME, subject_id="Toán", ai_mode=AIMode.STRICT.value,
                      class_code=class_code(db, "Toan10"))
        db.add(c)
        db.flush()
        db.add(ClassMember(class_id=c.id, student_id=student.id))

        md = "\n---page---\n".join("## %s\n%s" % (p["title"], p["text"]) for p in lesson).encode("utf-8")
        d = Document(class_id=c.id, file_name=DOC_NAME, file_key="", content_type="text/markdown", is_demo=True)
        db.add(d)
        db.flush()
        d.file_key = storage.put_file(f"classes/{c.id}/documents/{d.id}.md", md, "text/markdown")
        pages = extract_pages(md, DOC_NAME)
        save_pages_and_chunks(db, d, c, pages)
        d.status, d.page_count = DocStatus.READY.value, len(pages)

        for t in tasks:
            a = Assignment(class_id=c.id, due_at=datetime.fromisoformat(t["due_at"]).astimezone(timezone.utc),
                           allow_late=True, current_version=1)
            db.add(a)
            db.flush()
            db.add(AssignmentVersion(assignment_id=a.id, version=1, title="%s · %s" % (t["id"], t["title"]),
                                     prompt=t["question"], reference_answer=t["answer_key"]))
        db.commit()
        print("Đã nạp lớp '%s' (mã lớp %s): %d trang bài giảng, %d bài tập."
              % (CLASS_NAME, c.class_code, len(pages), len(tasks)))
        print("Đăng nhập: %s / %s (mật khẩu trong DEMO_PASSWORD của script này)" % (TEACHER["email"], STUDENT["email"]))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
