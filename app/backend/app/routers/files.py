"""Tải file gốc (PDF bài giảng, ảnh bài nộp) có kiểm tra quyền.

S3: chuyển hướng sang presigned URL ngắn hạn. Local: backend trả file trực tiếp.
"""
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core import storage
from app.core.security import CurrentUser, get_current_user
from app.db import get_db
from app.models import Assignment, Document, DocStatus, Submission
from app.routers.common import enrolled_class, owned_assignment, owned_class

router = APIRouter(prefix="/files", tags=["file"])


def _serve(key: str, filename: str | None, content_type: str | None):
    url = storage.presigned_url(key, expires=600)
    if url:
        return RedirectResponse(url)
    ctype = content_type or mimetypes.guess_type(key)[0] or "application/octet-stream"
    headers = {"Cache-Control": "private, max-age=300"}
    if filename:
        headers["Content-Disposition"] = f"inline; filename*=UTF-8''{_quote(filename)}"
    return Response(storage.read_file(key), media_type=ctype, headers=headers)


def _quote(s: str) -> str:
    from urllib.parse import quote

    return quote(s)


@router.get("/documents/{document_id}")
def document_file(document_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài liệu")
    if user.role == "teacher":
        owned_class(db, user, d.class_id)
    else:
        enrolled_class(db, user, d.class_id)
        if d.status != DocStatus.READY.value:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tài liệu chưa sẵn sàng")
    return _serve(d.file_key, d.file_name, d.content_type)


@router.get("/submissions/{submission_id}/image")
def submission_image(submission_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(Submission, submission_id)
    if not s or not s.image_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không có ảnh")
    if user.role == "teacher":
        owned_assignment(db, user, s.assignment_id)
    elif s.student_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền xem ảnh này")
    return _serve(s.image_key, None, None)


@router.get("/assignments/{assignment_id}/attachment")
def assignment_attachment(assignment_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if not a or not a.attachment_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bài tập không có file đề")
    if user.role == "teacher":
        owned_class(db, user, a.class_id)
    else:
        enrolled_class(db, user, a.class_id)
    return _serve(a.attachment_key, a.attachment_name, None)
