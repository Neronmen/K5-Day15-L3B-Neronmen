# Lộ trình (6 tuần)

Trạng thái: ✅ xong · 🟡 một phần · ⬜ chưa làm

## Giai đoạn 1 — Core LMS & Phân quyền ✅
- ✅ **Database** (PostgreSQL + pgvector): `users`, `classes`, `class_members`, `documents`, `document_pages`, `lecture_chunks`, `assignments` + `assignment_versions`, `submissions`, `grades`, `chat_messages`, `notifications`. Xem `backend/app/models.py`.
- ✅ **Auth & RBAC**: Email + mật khẩu, JWT; chặn quyền ở tầng API (chỉ chủ lớp thêm học sinh, upload tài liệu, duyệt điểm). `backend/app/core/security.py`, `backend/app/routers/common.py`.
- ✅ Google OAuth: nút "Đăng nhập với Google" (Google Identity Services), backend kiểm chữ ký ID token, liên kết với tài khoản sẵn có / học sinh được mời. Bật bằng `GOOGLE_CLIENT_ID`.
- ✅ **Teacher View**: tạo lớp, thêm học sinh qua email / CSV, tạo bài tập có deadline + rubric, phiên bản đề.
- ✅ **Student View**: danh sách lớp, tham gia bằng mã, xem đề, nộp bài text hoặc ảnh, bài nộp bị khoá.
- ✅ Alembic migration (`backend/migrations/`); container API chạy `alembic upgrade head` trước khi mở; test đảm bảo migration khớp models.

## Bổ sung — Thông báo lớp, lịch học, file đề ✅
- ✅ **Thông báo lớp**: thông báo chung / báo nghỉ (một buổi hoặc cả ngày) / báo học bù; ghim, xoá; học sinh nhận ở chuông, trang lớp và trang chủ. `backend/app/routers/teacher.py`, `frontend/src/components/AnnouncementForm.tsx`.
- ✅ **Lịch học**: buổi học lặp hằng tuần (thứ, giờ, phòng/link), chặn trùng giờ giữa các lớp của cùng giáo viên; trang **Lịch dạy** / **Lịch học** theo tuần, buổi nghỉ bị gạch, buổi học bù tự hiện; báo nghỉ ngay trên lịch. `backend/app/schedule.py`.
- ✅ **Xếp lớp** ở trang tổng quan theo buổi học sắp tới / tên / môn / mới tạo.
- ✅ **File đề bài tập** (PDF/Word): học sinh tải về; chữ trong file được đưa cho AI gia sư và AI chấm.
- ✅ **Trợ lý AI giáo viên** (`/teacher/assistant`): tìm kiếm nhanh theo từ khoá trong tài liệu mọi lớp (không tốn lượt AI);
  hỏi đáp, tóm tắt, đề cương ôn tập, câu hỏi ôn tập, dàn ý bài giảng có trích nguồn, bấm nguồn mở đúng trang;
  lưu bản tổng hợp thành tài liệu lớp. Giới hạn `TEACHER_AI_DAILY_LIMIT` (mặc định 100 lượt/ngày). `backend/app/routers/assistant.py`.
- ✅ **Tổng hợp tài liệu từ Google** (Trợ lý AI giáo viên → Tổng hợp từ: Google): AI rút yêu cầu thành truy vấn, tìm Google
  qua Serper (`SERPER_API_KEY`), đọc toàn văn 5 trang đầu (HTML/PDF, chặn địa chỉ nội bộ), tổng hợp có thẻ nguồn bấm mở link;
  thẻ nguồn bịa bị loại; lưu thành tài liệu lớp kèm danh sách link tham khảo. `backend/app/core/websearch.py`.

## Giai đoạn 2 — Pipeline nạp tri thức & Strict RAG ✅
- ✅ Upload → lưu Object Storage (local / MinIO / R2) → đẩy job (Celery khi `TASK_BACKEND=celery`, chạy nền trong API khi `inline`). `backend/app/tasks.py`, `backend/app/worker.py`.
- ✅ Bóc tách giữ `page_number`: PDF (pypdf, tự dùng Docling nếu cài), PPTX (theo slide), DOCX (theo ngắt trang / phần). Chunk kèm `class_id`, `teacher_id`, `subject_id`, `source_label`. `backend/app/ingestion/pipeline.py`.
- ✅ Tìm đoạn: BM25 không dấu (mặc định) hoặc pgvector khi bật `EMBEDDING_MODEL`. Luôn lọc cứng theo lớp. `backend/app/core/tenancy.py`.
- ✅ LangGraph **Retrieve → Relevance Grader → quyết định nhánh**; lớp khoá cứng không có nguồn thì trả lời cố định, không gọi model sinh văn bản. `backend/app/agents/knowledge_graph.py`.
- ✅ System prompt bắt buộc `[Nguồn: Tên_file - Trang X]`; nhánh `⚠️ [Kiến thức mở rộng ngoài bài giảng]` cho lớp mở rộng; backend loại thẻ nguồn bịa. `backend/app/agents/prompts.py`, `tutor.py`.
- ✅ Chat stream SSE + PDF Viewer đối chiếu: bấm thẻ nguồn → cuộn & đánh dấu đúng trang (PDF dùng react-pdf; Word/Slide hiện văn bản theo trang).
- ✅ Thông báo giáo viên khi tài liệu sẵn sàng / lỗi.

## Giai đoạn 3 — Agent giải & chấm bài ✅
- ✅ **Socratic Mode** trong khung bài tập (`is_assignment_context = True`), tính theo giờ server; đáp án mẫu chỉ vào ngữ cảnh sau hạn. `backend/app/agents/chat.py`, `policy.py`.
- ✅ **Auto-Grading**: ảnh → VLM (Gemini 2.5 Flash / Qwen-VL) → LaTeX; LangGraph trích xuất bước → kiểm tra logic → chấm nháp theo rubric. Chấm theo đúng phiên bản đề học sinh đã làm. `backend/app/grading/`.
- ✅ Màn hình duyệt điểm: xem bài, bản nháp AI từng bước, sửa điểm từng tiêu chí + nhận xét, Công bố; AI chấm lại.
- 🟡 Đọc ảnh viết tay cần khoá Gemini hoặc Qwen (chưa có thì bài ảnh chuyển "cần chấm tay").

## Giai đoạn 4 — Kiểm thử & chống lỗi ✅
1. ✅ Bảo mật & rò rỉ dữ liệu: test tự động học sinh Lớp A gọi API tài liệu / chat / bài tập / file của Lớp B (`backend/tests/`).
2. ✅ Prompt injection: test tự động (input luôn ở vai `user`, gắn cờ) + `scripts/eval_injection.py` với model thật — **8/8 an toàn** trên DeepSeek (22/11/2026).
3. ✅ Chịu tải: `scripts/load_test.py` — 40 học sinh nộp ảnh cùng lúc: 40/40 thành công, 0,76 giây (SQLite, 1 tiến trình). Chấm AI chạy qua hàng đợi Celery giới hạn 30 bài/phút/tiến trình.
4. ✅ Giới hạn chi phí: `CHAT_DAILY_LIMIT` lượt hỏi/ngày/học sinh; nén ảnh ≤1600px JPEG trước khi gửi VLM; ảnh mờ bị chặn ngay khi nộp.

## Giai đoạn 5 — Triển khai ✅ (cần chạy trên hạ tầng thật)
- ✅ Docker: `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` (db, redis, api, worker, web, caddy HTTPS, minio).
- ✅ Hướng dẫn Vercel + VPS / Railway / Render + Cloudflare R2 + tên miền: `docs/deployment.md`.
- ✅ Giám sát: Sentry (`SENTRY_DSN`), LangSmith (`LANGSMITH_*`).
- ✅ Onboarding: Lớp học mẫu tự tạo cho giáo viên mới.
- ⬜ Thuê VPS, trỏ tên miền, tạo bucket R2 — việc của chủ dự án (xem `docs/deployment.md`).
