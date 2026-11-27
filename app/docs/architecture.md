# Kiến trúc Công nghệ

Mô hình **Modular Monolith + Async Worker**: một backend FastAPI chia module rõ ràng, tác vụ nặng chạy ở worker Celery. Đi từ MVP lên quy mô lớn không cần viết lại.

```
+-------------------------------------------------------------------+
|                     FRONTEND (Next.js / React)                    |
|  - Teacher Portal (Quản lý lớp, Duyệt điểm, Upload tài liệu)      |
|  - Student Portal (Xem tài liệu, Nộp bài ảnh/text, Chat Agent)    |
+---------------------------------+---------------------------------+
                                  | REST API / SSE (Streaming Chat)
                                  v
+-------------------------------------------------------------------+
|                   API GATEWAY & BACKEND (FastAPI)                 |
|  - Auth & RBAC (Role: Teacher / Student)                          |
|  - LMS Core Service (Lớp học, Thành viên, Bài tập, Điểm số)       |
+----------------+--------------------------------+-----------------+
                 | Đẩy tác vụ nặng                | Truy vấn nhanh
                 v                                v
+--------------------------------+  +-------------------------------+
|  ASYNC WORKER (Celery + Redis) |  |  AI ORCHESTRATOR (LangGraph)  |
|  - Parse PDF/Slide (Docling)   |  |  - Knowledge Agent (RAG)      |
|  - Tạo Embeddings              |  |  - Socratic Tutor Agent       |
|  - Chấm bài hàng loạt (Batch)  |  |  - Auto-Grading Agent         |
+----------------+---------------+  +---------------+---------------+
                 +----------------+-----------------+
                                  v
+-------------------------------------------------------------------+
|                        DATA & STORAGE LAYER                       |
|  - PostgreSQL + pgvector : dữ liệu quan hệ & vector tài liệu      |
|  - Object Storage (MinIO / S3 / R2) : file PDF gốc & ảnh bài nộp  |
+-------------------------------------------------------------------+
```

## Tech stack & vị trí trong code

| Tầng | Lựa chọn | Code |
|---|---|---|
| Frontend | Next.js (App Router) + Tailwind CSS + shadcn/ui | `frontend/` |
| Đọc PDF trong web | React-PDF / PDF.js, cuộn & highlight đúng trang khi bấm `[Nguồn: ...]` | `frontend/` (TODO) |
| Công thức | KaTeX | `frontend/` (TODO) |
| Backend | Python 3.11 + FastAPI, chat stream qua SSE | `backend/app/main.py` |
| Auth & RBAC | Middleware kiểm tra token + quyền sở hữu lớp. API chat học sinh luôn gắn `strict_tutor_mode` | `backend/app/core/security.py` |
| Orchestration | LangGraph: Knowledge Agent có **Relevance Grader**, Socratic Tutor, chấm bài 3 bước | `backend/app/agents/knowledge_graph.py`, `backend/app/grading/graph.py` |
| Parse tài liệu | Docling (hoặc MinerU): PDF/Slide → Markdown sạch, giữ số trang | `backend/app/ingestion/pipeline.py` |
| VLM đọc ảnh & chấm bài | Gemini 2.5 Flash hoặc Qwen2.5-VL | `backend/app/core/llm.py` (`MODEL_VISION`, `MODEL_GRADING`) |
| Embedding | `bge-m3` hoặc `text-embedding-3-small` | `backend/app/core/llm.py` (`EMBEDDING_MODEL`) |
| Database | PostgreSQL + pgvector, `JOIN` lọc vector theo `class_id` | `backend/app/models.py`, `backend/app/core/tenancy.py` |
| Hàng đợi | Redis + Celery (PDF 100 trang, 40 bài nộp cùng lúc) | `backend/app/worker.py` |
| Lưu file | MinIO (self-host) hoặc S3 / Cloudflare R2 | `backend/app/core/storage.py` |

## Luồng Knowledge Agent (LangGraph)
`retrieve` (lọc theo lớp, Rule 2) → `grade_relevance` (bỏ đoạn không liên quan) → nếu không còn đoạn nào: trả "không tìm thấy trong bài giảng" (lớp khoá cứng) hoặc cho phép nguồn ngoài có nhãn (lớp mở rộng) → `generate` (trả lời kèm `[Nguồn: Tên_file - Trang X]`, áp Socratic Mode nếu là học sinh hỏi bài còn hạn).

## Luồng chấm bài (LangGraph, chạy ở Celery)
`ingest` (VLM đọc ảnh → LaTeX, ảnh mờ thì từ chối) → `extractor` → `logic_verifier` → `rubric_scorer` → lưu điểm `pending_review` (Rule 4).

## Model routing
Mỗi tác vụ có một model riêng trong `.env`; đổi nhà cung cấp không phải sửa luồng.

| Tác vụ | Biến | Mặc định |
|---|---|---|
| Chat thường, trắc nghiệm | `MODEL_CHAT` | model nhỏ, rẻ |
| Đọc ảnh viết tay | `MODEL_VISION` | `gemini-2.5-flash` |
| Chấm tự luận | `MODEL_GRADING` | `gemini-2.5-flash` |
| Embedding | `EMBEDDING_MODEL` | `bge-m3` |
