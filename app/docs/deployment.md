# Triển khai MinutesStudy

Mục tiêu: người dùng truy cập qua tên miền chính thức trên máy tính và điện thoại, chi phí MVP thấp.

```
Trình duyệt ──► minutesstudy.vn  (Vercel: Next.js, SSL tự động)
           └──► api.minutesstudy.vn (VPS: Caddy HTTPS → FastAPI ─► Celery worker)
                                          │                    │
                                   PostgreSQL+pgvector      Redis
                                          └── File: Cloudflare R2
```

## 1. Chuẩn bị khoá & cấu hình
Sao chép `.env.example` thành `.env` trên VPS và đổi tối thiểu:

| Biến | Giá trị production |
|---|---|
| `JWT_SECRET` | chuỗi ngẫu nhiên dài: `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `POSTGRES_PASSWORD` | mật khẩu mạnh (docker compose dùng biến này cho DB) |
| `CORS_ORIGINS` | `https://minutesstudy.vn` |
| `DEEPSEEK_API_KEY` | khoá DeepSeek |
| `MODEL_VISION` + `GEMINI_API_KEY` (hoặc `QWEN_API_KEY`) | để AI đọc ảnh bài làm viết tay |
| `STORAGE_BACKEND=s3`, `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Cloudflare R2 |
| `GOOGLE_CLIENT_ID` | (tuỳ chọn) OAuth Client ID loại Web; thêm `https://minutesstudy.vn` vào Authorized JavaScript origins |
| `SENTRY_DSN` | (tuỳ chọn) theo dõi lỗi |

`TASK_BACKEND=celery`, `DATABASE_URL`/`REDIS_URL` và `AUTO_CREATE_TABLES=false` đã được `docker-compose.yml` đặt sẵn. Schema DB do Alembic quản lý: container `api` tự chạy `alembic upgrade head` (tạo bảng + extension `vector`) mỗi lần khởi động.

Sửa `backend/app/models.py` → tạo migration mới: `cd backend && alembic revision --autogenerate -m "mo ta"`, kiểm tra file sinh ra rồi commit.

## 2. Backend + DB + Worker trên VPS
VPS tối thiểu 4GB RAM (8GB nếu bật Docling/bge-m3), Ubuntu 22.04+, đã cài Docker.

```bash
git clone <repo> minutesstudy && cd minutesstudy
cp .env.example .env && nano .env
DOMAIN=minutesstudy.vn docker compose --profile proxy up -d --build
docker compose logs -f api worker
```

- Caddy (`deploy/Caddyfile`) tự cấp HTTPS cho `api.minutesstudy.vn`. Trỏ bản ghi **A** của `api` (và tên miền chính nếu tự host frontend) về IP VPS trước.
- Postgres/Redis chỉ mở ở `127.0.0.1`, không lộ ra Internet.
- Tăng sức chấm bài: sửa `--concurrency` của `worker` hoặc `docker compose up -d --scale worker=2`.

Railway / Render: tạo 2 service từ thư mục `backend` (lệnh API mặc định của Dockerfile, và worker với lệnh `celery -A app.worker worker --concurrency=4`), thêm Postgres có pgvector và Redis do nền tảng cung cấp, đặt biến môi trường như bảng trên.

## 3. Frontend trên Vercel
1. Import repo trên Vercel, **Root Directory** = `frontend`.
2. Biến môi trường: `NEXT_PUBLIC_API_URL=https://api.minutesstudy.vn`.
3. Thêm tên miền `minutesstudy.vn` trong Settings → Domains, làm theo hướng dẫn DNS của Vercel.

Tự host frontend trên cùng VPS thay vì Vercel:
```bash
PUBLIC_API_URL=https://api.minutesstudy.vn DOMAIN=minutesstudy.vn docker compose --profile web --profile proxy up -d --build
```

## 4. File trên Cloudflare R2
1. R2 → Create bucket `minutesstudy` (để private).
2. Manage R2 API Tokens → quyền Object Read & Write cho bucket.
3. `.env`: `STORAGE_BACKEND=s3`, `S3_ENDPOINT=https://<account_id>.r2.cloudflarestorage.com`, `S3_BUCKET=minutesstudy`, khoá vừa tạo.

Học sinh/giáo viên tải file qua `/files/...`: backend kiểm tra quyền rồi chuyển hướng sang link R2 ký sẵn 10 phút.

## 5. Giám sát
- **Sentry**: `pip install ".[monitoring]"` (Dockerfile đã cài sẵn), đặt `SENTRY_DSN`.
- **LangSmith**: theo dõi từng bước của LangGraph (retrieve, relevance grader, chấm bài) để soát câu trả lời sai/ảo giác. Đặt `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT=minutesstudy`.
- Xem lại câu hỏi bị gắn cờ: giáo viên mở tab **Lịch sử hỏi AI** → "Chỉ tin nhắn bị gắn cờ".

## 6. Kiểm thử trước khi mở cho người ngoài (Giai đoạn 4)
```bash
cd backend
pytest                                                   # 52 test: cách ly lớp, injection, hạn mức, chấm bài…
python scripts/eval_injection.py --api https://api.minutesstudy.vn   # tấn công prompt với model thật
python scripts/load_test.py --api https://api.minutesstudy.vn --students 40 --image --wait-grading
```

## 7. Onboarding
Giáo viên mới đăng ký được tạo sẵn **Lớp học mẫu - Toán 11** (bài giảng mẫu đã sẵn sàng cho AI + bài tập mẫu có rubric). Tắt bằng `DEMO_CLASS_ON_SIGNUP=false`.

## Sao lưu
```bash
docker compose exec db pg_dump -U minutes minutesstudy | gzip > backup-$(date +%F).sql.gz
```
