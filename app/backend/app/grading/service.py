"""Rule 4: điểm AI chỉ là bản nháp chờ giáo viên duyệt."""
import json
import logging

from app.core import llm, storage
from app.db import SessionLocal
from app.models import AIGradeStatus, AssignmentVersion, Assignment, Grade, GradeStatus, Submission

from .graph import build_graph

log = logging.getLogger(__name__)
MIME = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".heic": "image/heic"}


def mark_queued(db, submission_id: str) -> None:
    g = db.get(Grade, submission_id) or Grade(submission_id=submission_id, status=GradeStatus.PENDING_REVIEW.value)
    g.ai_status, g.ai_error = AIGradeStatus.QUEUED.value, None
    db.merge(g)
    db.commit()


def run_ai_grading(submission_id: str) -> None:
    db = SessionLocal()
    try:
        s = db.get(Submission, submission_id)
        if not s:
            return
        g = db.get(Grade, s.id) or Grade(submission_id=s.id, status=GradeStatus.PENDING_REVIEW.value)
        if g.status == GradeStatus.PUBLISHED.value:
            return  # giáo viên đã công bố: không ghi đè
        g.ai_status, g.ai_error = AIGradeStatus.RUNNING.value, None
        db.merge(g)
        db.commit()

        if not llm.provider_ready(llm.Task.GRADING):
            _finish(db, s.id, AIGradeStatus.MANUAL, error="Chưa cấu hình khoá API cho MODEL_GRADING.")
            return
        a = db.get(Assignment, s.assignment_id)
        v = db.get(AssignmentVersion, (a.id, s.assignment_version))  # chấm theo đúng phiên bản đề học sinh đã làm
        image = None
        if s.image_key:
            image = storage.read_file(s.image_key)
        state = {
            "title": v.title, "prompt": a.full_prompt(v.prompt), "rubric": v.rubric, "reference_answer": v.reference_answer,
            "text": s.content, "image": image,
            "image_mime": MIME.get("." + s.image_key.rsplit(".", 1)[-1].lower()) if s.image_key else None,
        }
        try:
            out = build_graph().invoke(state)
        except Exception as e:  # noqa: BLE001
            log.exception("chấm bài %s lỗi", s.id)
            _finish(db, s.id, AIGradeStatus.FAILED, error=f"AI chấm lỗi: {type(e).__name__}: {str(e)[:300]}")
            return
        breakdown = {
            "ocr_text": out.get("ocr_text"), "image_confidence": out.get("image_confidence"),
            "steps": out.get("steps", []), "checks": out.get("checks", []), "items": out.get("items", []),
            "summary": out.get("summary", ""), "feedback": out.get("feedback", ""),
        }
        if out.get("rejected_reason"):
            _finish(db, s.id, AIGradeStatus.MANUAL, error=out["rejected_reason"], breakdown=breakdown)
        else:
            _finish(db, s.id, AIGradeStatus.DONE, score=out.get("total"), breakdown=breakdown)
    finally:
        db.close()


def _finish(db, submission_id: str, st: AIGradeStatus, *, score=None, breakdown=None, error=None) -> None:
    g = db.get(Grade, submission_id)
    if g.status == GradeStatus.PUBLISHED.value:
        return
    g.ai_status, g.ai_score, g.ai_error = st.value, score, error
    g.ai_breakdown = json.dumps(breakdown, ensure_ascii=False) if breakdown is not None else g.ai_breakdown
    g.status = GradeStatus.PENDING_REVIEW.value  # Rule 4
    db.commit()


def publish_grade(db, grade: Grade, teacher_id: str) -> None:
    """Chỉ gọi khi giáo viên bấm xác nhận."""
    grade.status = GradeStatus.PUBLISHED.value
    grade.reviewed_by = teacher_id
    db.commit()
