"""Đẩy tác vụ nặng ra khỏi request.

TASK_BACKEND=celery: gửi vào Redis cho worker (production, chịu tải 30–40 bài nộp cùng lúc).
TASK_BACKEND=inline: chạy nền ngay trong tiến trình API (dev, không cần Redis).
"""
from fastapi import BackgroundTasks

from app.core.config import settings


def enqueue_ingest(bg: BackgroundTasks, document_id: str) -> None:
    if settings.task_backend == "celery":
        from app.worker import ingest_document

        ingest_document.delay(document_id)
    else:
        from app.ingestion.pipeline import ingest_document

        bg.add_task(ingest_document, document_id)


def enqueue_grade(bg: BackgroundTasks, submission_id: str) -> None:
    if settings.task_backend == "celery":
        from app.worker import grade_submission

        grade_submission.delay(submission_id)
    else:
        from app.grading.service import run_ai_grading

        bg.add_task(run_ai_grading, submission_id)
