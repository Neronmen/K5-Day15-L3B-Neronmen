# Backend MinutesStudy: dùng chung image cho API (uvicorn) và worker (celery)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Cài thư viện trước để tận dụng cache khi chỉ sửa code
COPY pyproject.toml ./
ARG EXTRAS="monitoring"
RUN mkdir app && touch app/__init__.py \
 && pip install ".[${EXTRAS}]" \
 && rm -rf app

COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./
COPY migrations ./migrations

RUN useradd --create-home --uid 1000 minutes && mkdir -p /app/storage && chown -R minutes /app
USER minutes

EXPOSE 8000
# Cập nhật schema DB (Alembic) rồi mới mở API. PORT do Render/Railway cấp; WEB_CONCURRENCY=1 cho gói RAM nhỏ
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --proxy-headers --forwarded-allow-ips '*'"]
