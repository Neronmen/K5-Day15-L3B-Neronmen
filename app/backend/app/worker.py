"""Worker Celery: chạy bóc tách tài liệu và chấm bài ngoài tiến trình API.

Chạy: celery -A app.worker worker --loglevel=info --concurrency=4
"""
from celery import Celery

from app.core.config import settings

celery = Celery("minutesstudy", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(
    task_acks_late=True,              # worker chết giữa chừng → job được giao lại
    worker_prefetch_multiplier=1,     # chia đều bài nộp cho các worker khi cả lớp nộp sát deadline
    task_time_limit=600,
    broker_connection_retry_on_startup=True,
)


@celery.task(bind=True, max_retries=3, default_retry_delay=20, rate_limit="30/m")
def grade_submission(self, submission_id: str) -> None:
    from app.grading.service import run_ai_grading

    run_ai_grading(submission_id)


@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def ingest_document(self, document_id: str) -> None:
    from app.ingestion.pipeline import ingest_document as run

    run(document_id)
