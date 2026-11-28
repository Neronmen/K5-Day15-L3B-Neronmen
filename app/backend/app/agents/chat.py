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
from app.models import Assignment, AssignmentVersion, ChatMessage, ClassMember, Classroom, Document

from . import core_bridge, knowledge_graph
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
    route: str                     # answer | extended | no_source | core (khung bài tập qua lõi codebase/, N-08)
    system: str
    messages: list[dict]
    chunks: list[dict]
    document_id: str | None = None
    assignment_id: str | None = None
    meta: dict = field(default_factory=dict)
    core: dict | None = None       # route "core": tham số cho core_bridge.answer
    guard: list[str] | None = None  # luồng bài giảng cũ: có bài còn hạn → không stream từng mẩu, soi cả câu trước khi gửi


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
    if assignment is not None and core_bridge.available():
        return _plan_core(db, student_id=student_id, cls=cls, question=question, assignment=assignment,
                          remaining=remaining)
    if document is not None and core_bridge.available():
        guarded = _plan_lecture_guard(db, student_id=student_id, cls=cls, question=question, document=document,
                                      remaining=remaining)
        if guarded:
            return guarded

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
    guard = None
    if document is not None and core_bridge.available():  # khung bài giảng: soi đáp án mọi bài còn hạn trước khi gửi
        guard = core_bridge.guard_finals(
            [a["reference_answer"] for a in _open_assignments(db, student_id, None, datetime.now(timezone.utc))],
            None) or None
    return ChatPlan(guard=guard,
        class_id=cls.id, student_id=student_id, mode=mode, route=route, system=system,
        messages=[*history, {"role": "user", "content": question}], chunks=chunks,
        document_id=document.id if document else None, assignment_id=assignment.id if assignment else None,
        meta={"remaining_today": remaining},
    )


def _plan_core(db: Session, *, student_id: str, cls: Classroom, question: str, assignment: Assignment,
               remaining: int) -> ChatPlan:
    """Khung bài tập qua lõi codebase/ (N-08): chế độ, gắn cờ, prompt, tìm đoạn, citations, check_leak đều của lõi."""
    v = db.get(AssignmentVersion, (assignment.id, assignment.current_version))
    now = datetime.now(timezone.utc)
    mode = core_bridge.tutor_mode(_aware(assignment.due_at), now)  # Rule 3, giờ server
    core = {"cls": cls, "mode": mode, "title": v.title, "prompt": assignment.full_prompt(v.prompt),
            "reference_answer": v.reference_answer, "question": question}
    meta = {"remaining_today": remaining}
    # Học sinh dán đề của một bài KHÁC còn hạn (vd mở bài đã hết hạn để xin giải bài ngày mai): lượt này chuyển về
    # chế độ gợi ý theo đúng bài còn hạn đó — đề, đoạn bài giảng và check_leak đều lấy theo bài đó.
    open_list = _open_assignments(db, student_id, assignment.id, now)
    match = _open_match(db, student_id, question, assignment.id, now, open_list)
    if match:
        mode = "hint"
        core.update(_core_for_match(match))
        meta["same_as"] = match["title"]
    # Chốt chặn cuối: dù so đề không nhận ra (vd đề viết bằng chữ), câu trả lời không được chứa đáp án bài còn hạn khác
    core["guard"] = core_bridge.guard_finals(
        [a["reference_answer"] for a in open_list if not match or a["id"] != match["id"]], core["reference_answer"])
    core["history"] = _history(db, student_id, None, assignment.id)
    db.add(ChatMessage(class_id=cls.id, assignment_id=assignment.id, student_id=student_id, role="user", mode=mode,
                       content=question, flagged=core_bridge.flag(question, mode)))
    db.commit()
    return ChatPlan(
        class_id=cls.id, student_id=student_id, mode=mode, route="core", system="", messages=[], chunks=[],
        assignment_id=assignment.id, meta=meta, core=core,
    )


def _plan_lecture_guard(db: Session, *, student_id: str, cls: Classroom, question: str, document: Document,
                        remaining: int) -> ChatPlan | None:
    """Khung hỏi bài giảng: tin nhắn chứa đề của một bài CÒN HẠN → không để Knowledge Agent giải; trả lời qua lõi ở
    chế độ gợi ý theo đúng bài đó (như khi hỏi trong khung bài tập). Không trùng → None, chạy luồng bài giảng cũ."""
    open_list = _open_assignments(db, student_id, None, datetime.now(timezone.utc))
    match = _open_match(db, student_id, question, None, datetime.now(timezone.utc), open_list)
    if not match:
        return None
    core = {"question": question, "history": _history(db, student_id, document.id, None), **_core_for_match(match)}
    core["guard"] = core_bridge.guard_finals([a["reference_answer"] for a in open_list if a["id"] != match["id"]],
                                             match["reference_answer"])
    db.add(ChatMessage(class_id=cls.id, document_id=document.id, student_id=student_id, role="user", mode="hint",
                       content=question, flagged=core_bridge.flag(question, "hint")))
    db.commit()
    return ChatPlan(
        class_id=cls.id, student_id=student_id, mode="hint", route="core", system="", messages=[], chunks=[],
        document_id=document.id, meta={"remaining_today": remaining, "same_as": match["title"]}, core=core,
    )


def _open_match(db: Session, student_id: str, question: str, exclude_id: str | None, now: datetime,
                open_list: list[dict] | None = None) -> dict | None:
    if open_list is None:
        open_list = _open_assignments(db, student_id, exclude_id, now)
    match = next(iter(core_bridge.open_matches(question, open_list)), None)
    if match:
        log.info("core tutor: tin nhắn trùng đề bài còn hạn %s → chế độ gợi ý", match["id"])
    return match


def _core_for_match(match: dict) -> dict:
    """Tham số core_bridge.answer khi học sinh dán đề của bài còn hạn: đề, lớp, đáp án (chỉ cho check_leak) của bài đó."""
    due_vn = _aware(match["due_at"]).astimezone(VN_TZ).strftime("%H:%M %d/%m/%Y")
    return {"cls": match["cls"], "mode": "hint", "title": match["title"], "prompt": match["question"],
            "reference_answer": match["reference_answer"],
            "notice": (f"Đề học sinh gửi trùng với bài \"{match['title']}\" đang còn hạn nộp đến {due_vn}. "
                       "Áp dụng CHẾ ĐỘ GỢI Ý cho đề này như khi bài còn hạn: không giải hết, không nêu đáp số; "
                       "nói ngắn gọn cho em biết đề này thuộc bài đang còn hạn rồi gợi ý bước đầu.")}


def _open_assignments(db: Session, student_id: str, exclude_id: str | None, now: datetime) -> list[dict]:
    """Bài còn hạn ở MỌI lớp học sinh đang học (trừ bài đang mở), kèm đề hiện hành để so với tin nhắn."""
    rows = db.execute(
        select(Assignment, AssignmentVersion, Classroom)
        .join(ClassMember, ClassMember.class_id == Assignment.class_id)
        .join(AssignmentVersion, (AssignmentVersion.assignment_id == Assignment.id)
              & (AssignmentVersion.version == Assignment.current_version))
        .join(Classroom, Classroom.id == Assignment.class_id)
        .where(ClassMember.student_id == student_id, *([Assignment.id != exclude_id] if exclude_id else []))
    ).all()
    return [{"id": a.id, "title": v.title, "question": a.full_prompt(v.prompt), "reference_answer": v.reference_answer,
             "due_at": a.due_at, "cls": c} for a, v, c in rows if _aware(a.due_at) > now]


def _core_stream(plan: ChatPlan) -> Iterator[str]:
    """Không stream từng mẩu: chế độ hint phải chạy check_leak trên CẢ câu trả lời trước khi học sinh thấy."""
    yield _sse({"type": "start", "mode": plan.mode, "route": plan.route, **plan.meta})
    db = SessionLocal()
    failed = False
    try:
        try:
            out = core_bridge.answer(db, **plan.core)
            for n in out["notes"]:
                log.info("core tutor: %s", n)
        except Exception as e:  # noqa: BLE001
            log.exception("core tutor lỗi")
            failed = True
            out = {"text": f"(lỗi: {type(e).__name__})", "decision": None, "citations": []}
            yield _sse({"type": "error", "message": "Trợ lý AI đang bận hoặc lỗi kết nối, em thử lại sau ít phút."})
        if not failed:
            yield _sse({"type": "delta", "text": out["text"]})
        db.add(ChatMessage(class_id=plan.class_id, document_id=plan.document_id, assignment_id=plan.assignment_id,
                           student_id=plan.student_id, role="assistant", mode=plan.mode, content=out["text"],
                           citations=json.dumps(out["citations"], ensure_ascii=False)))
        db.commit()
    finally:
        db.close()
    if not failed:
        yield _sse({"type": "done", "citations": out["citations"], "mode": plan.mode, "route": plan.route,
                    "decision": out["decision"]})


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def sse_stream(plan: ChatPlan) -> Iterator[str]:
    if plan.route == "core":
        yield from _core_stream(plan)
        return
    yield _sse({"type": "start", "mode": plan.mode, "route": plan.route, **plan.meta})
    text, failed = "", False
    if plan.route == "no_source":
        text = NOT_FOUND
        yield _sse({"type": "delta", "text": text})
    else:
        try:
            for piece in llm.stream(llm.Task.CHAT, plan.system, plan.messages):
                text += piece
                if not plan.guard:
                    yield _sse({"type": "delta", "text": piece})
            if plan.guard:  # có bài còn hạn: chỉ gửi khi cả câu không chứa đáp án của các bài đó
                if core_bridge.leaks(text, plan.guard):
                    log.info("lecture chat: câu trả lời chứa đáp án bài còn hạn → thay bằng câu cố định")
                    text = core_bridge.SAFE_TEXT
                yield _sse({"type": "delta", "text": text})
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
