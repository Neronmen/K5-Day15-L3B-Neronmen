# MinutesStudy

Nền tảng kết nối **giáo viên** và **học viên**, có trợ lý AI học tập và chấm bài.

## Chức năng
- **Giáo viên**: đăng bài giảng / tài liệu, giao bài tập có deadline, rubric và đáp án mẫu, duyệt điểm AI chấm, xem lịch sử hỏi AI của học viên; Trợ lý AI tổng hợp tài liệu của lớp hoặc tìm trên Google, luôn kèm nguồn.
- **Học viên**: xem bài giảng & bài tập, nộp bài (gõ hoặc chụp ảnh vở), hỏi trợ lý AI.

## Luật cốt lõi
- AI chỉ dùng kiến thức từ bài giảng giáo viên đăng, luôn ghi nguồn, không bịa.
- Bài tập còn hạn: AI chỉ gợi ý. Hết hạn: AI mới được đưa đáp án.
- Điểm AI chấm luôn chờ giáo viên duyệt.
- Dữ liệu giữa các lớp tách biệt tuyệt đối.

Luồng người dùng: [docs/user-flows.md](docs/user-flows.md) · Rules: [docs/rules.md](docs/rules.md) · Kiến trúc: [docs/architecture.md](docs/architecture.md) · Lộ trình: [docs/roadmap.md](docs/roadmap.md)

## Cấu trúc
```
frontend/   Next.js 15 + Tailwind 4, React-PDF, KaTeX, chat SSE
backend/    FastAPI + LangGraph + Celery (Python 3.11+), DeepSeek / Gemini / Qwen
            PostgreSQL + pgvector, Redis, local / MinIO / Cloudflare R2
deploy/     Caddyfile (HTTPS tự động trên VPS)
docs/       Rules, kiến trúc, lộ trình, triển khai
```

## Chạy trên máy (không cần Docker)
```bash
cp .env.example .env                      # điền DEEPSEEK_API_KEY
cd backend
python -m venv .venv && .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload   # API: http://localhost:8000/docs
cd ../frontend && npm install && npm run dev                     # Web: http://localhost:3000
```
Đăng ký tài khoản giáo viên là có sẵn **Lớp học mẫu** (bài giảng + bài tập) để thử AI ngay.
Ở chế độ này hàng đợi chạy nền trong API (`TASK_BACKEND=inline`), file lưu ở `backend/storage/`, bảng tự tạo khi khởi động.
Đăng nhập Google: điền `GOOGLE_CLIENT_ID` trong `.env` (xem [docs/deployment.md](docs/deployment.md)).

## Chạy đầy đủ với Docker (Postgres + Redis + Celery worker)
```bash
docker compose up -d --build              # db, redis, api, worker
docker compose --profile web up -d --build   # thêm frontend ở cổng 3000
```

## Kiểm thử
```bash
cd backend
pytest                                    # 52 test: RBAC, cách ly lớp, RAG có nguồn, Socratic, injection, chấm bài
python scripts/eval_injection.py          # tấn công prompt với model thật (cần backend đang chạy)
python scripts/load_test.py --students 40 --image   # 40 học sinh nộp ảnh cùng lúc
```

Triển khai lên VPS / Vercel / R2 với tên miền: [docs/deployment.md](docs/deployment.md).
