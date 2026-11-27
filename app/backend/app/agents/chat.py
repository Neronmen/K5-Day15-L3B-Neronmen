"""Luồng chat của học sinh: kiểm tra hạn mức → graph RAG → stream SSE → lưu hội thoại.

Dùng chung cho chat bên bài giảng (Knowledge Agent) và khung bài tập (Socratic Tutor).
"""
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import llm
from app.core.config import settings
from app.core.tenancy import TenantScope
from app.db import SessionLocal
from app.models import Assignment, AssignmentVersion, ChatMessage, Classroom, Document

from . import knowledge_graph
from .policy import get_tutor_mode
from .prompts import NOT_FOUND
from .tutor import AssignmentCtx, build_system, citations, flag_message

log = logging.getLogger(__name__)
VN_TZ = timezone(timedelta(hours=7))
HISTORY_TURNS = 6


@dataclass
class ChatPlan:
    class_id: str
    student_id: str
    mode: str                      # lecture | hint | answer
    route: str                     # answer | extended | no_source
    system: str
    messages: list[dict]
    chunks: list[dict]
    document_id: str | None = None
    assignment_id: str | None = None
    meta: dict = field(default_factory=dict)


def _check_quota(db: Session, student_id: str) -> int:
    start = datetime.now(VN_TZ).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    used = db.scalar(select(func.count()).select_from(ChatMessage).where(
        ChatMessage.student_id == student_id, ChatMessage.role == "user", ChatMessage.created_at >= start))
    if used >= settings.chat_daily_limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"Em đã dùng hết {settings.chat_daily_limit} lượt hỏi AI hôm nay. Lượt hỏi được làm mới lúc 0 giờ.")
    return settings.chat_daily_limit - used - 1


def _history(db: Session, student_id: str, document_id: str | None, assignment_id: str | None) -> list[dict]:
    stmt = select(ChatMessage).where(ChatMessage.student_id == student_id)
    stmt = stmt.where(ChatMessage.assignment_id == assignment_id) if assignment_id else \
        stmt.where(ChatMessage.document_id == document_id, ChatMessage.assignment_id.is_(None))
    rows = list(db.scalars(stmt.order_by(ChatMessage.created_at.desc()).limit(HISTORY_TURNS * 2)))
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def plan_chat(db: Session, *, student_id: str, cls: Classroom, question: str,
              document: Document | None = None, assignment: Assignment | None = None) -> ChatPlan:
    question = question.strip()
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Câu hỏi trống")
    if len(question) > 4000:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Câu hỏi quá dài (tối đa 4000 ký tự)")
    if not llm.provider_ready(llm.Task.CHAT):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Trợ lý AI chưa được cấu hình khoá API.")
    remaining = _check_quota(db, student_id)

    ctx = None
    mode = "lecture"
    search_query = question
    if assignment is not None:
        mode = get_tutor_mode("student", _aware(assignment.due_at))  # Rule 3, giờ server
        v = db.get(AssignmentVersion, (assignment.id, assignment.current_version))
        prompt = assignment.full_prompt(v.prompt)
        ctx = AssignmentCtx(title=v.title, prompt=prompt, reference_answer=v.reference_answer)
        search_query = f"{question}\n{v.title}\n{prompt[:500]}"

    history = _history(db, student_id, document.id if document else None, assignment.id if assignment else None)
    state = knowledge_graph.run(
        db, question=question, search_query=search_query,
        scope=TenantScope(cls.teacher_id, cls.id, cls.subject_id), ai_mode=cls.ai_mode,
        document_id=document.id if document else None,
    )
    route = state.get("route", "no_source")
    # Khung bài tập: luôn để model trả lời (gợi ý dựa trên đề) kể cả khi không có đoạn tài liệu khớp
    if assignment is not None and route == "no_source":
        route = "answer"
    chunks = state.get("relevant") or []
    system = build_system(chunks=chunks, ai_mode=cls.ai_mode,
                          mode=None if assignment is None else mode, assignment=ctx)

    db.add(ChatMessage(class_id=cls.id, document_id=document.id if document else None,
                       assignment_id=assignment.id if assignment else None, student_id=student_id,
                       role="user", mode=mode, content=question, flagged=flag_message(question, mode)))
    db.commit()
    return ChatPlan(
        class_id=cls.id, student_id=student_id, mode=mode, route=route, system=system,
        messages=[*history, {"role": "user", "content": question}], chunks=chunks,
        document_id=document.id if document else None, assignment_id=assignment.id if assignment else None,
        meta={"remaining_today": remaining},
    )


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def sse_stream(plan: ChatPlan) -> Iterator[str]:
    yield _sse({"type": "start", "mode": plan.mode, "route": plan.route, **plan.meta})
    text, failed = "", False
    if plan.route == "no_source":
        text = NOT_FOUND
        yield _sse({"type": "delta", "text": text})
    else:
        try:
            for piece in llm.stream(llm.Task.CHAT, plan.system, plan.messages):
                text += piece
                yield _sse({"type": "delta", "text": piece})
        except Exception as e:  # noqa: BLE001
            log.exception("chat stream lỗi")
            failed = True
            yield _sse({"type": "error", "message": "Trợ lý AI đang bận hoặc lỗi kết nối, em thử lại sau ít phút."})
            text = text or f"(lỗi: {type(e).__name__})"
    cites = citations(text, plan.chunks)
    db = SessionLocal()
    try:
        db.add(ChatMessage(class_id=plan.class_id, document_id=plan.document_id, assignment_id=plan.assignment_id,
                           student_id=plan.student_id, role="assistant", mode=plan.mode, content=text,
                           citations=json.dumps(cites, ensure_ascii=False)))
        db.commit()
    finally:
        db.close()
    if not failed:
        yield _sse({"type": "done", "citations": cites, "mode": plan.mode, "route": plan.route})
