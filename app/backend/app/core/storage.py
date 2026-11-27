"""Lưu file gốc & ảnh bài nộp.

STORAGE_BACKEND=local: ghi vào thư mục LOCAL_STORAGE_DIR (dev, không cần MinIO).
STORAGE_BACKEND=s3: MinIO / S3 / Cloudflare R2 (cùng API S3).
"""
from pathlib import Path

from .config import settings


def _s3():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


def put_file(key: str, data: bytes, content_type: str | None) -> str:
    if settings.storage_backend == "s3":
        _s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type or "application/octet-stream")
    else:
        path = Path(settings.local_storage_dir) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return key


def read_file(key: str) -> bytes:
    if settings.storage_backend == "s3":
        return _s3().get_object(Bucket=settings.s3_bucket, Key=key)["Body"].read()
    return (Path(settings.local_storage_dir) / key).read_bytes()


def presigned_url(key: str, expires: int = 3600) -> str | None:
    """Link tải trực tiếp (chỉ có với S3). Local thì backend tự phục vụ file."""
    if settings.storage_backend != "s3":
        return None
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=expires
    )
