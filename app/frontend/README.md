# Frontend

Next.js 15 (App Router) + Tailwind CSS 4. Gọi backend qua `NEXT_PUBLIC_API_URL` (mặc định `http://localhost:8000`).

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # kiểm tra build production
```

## Trang
| Trang | Đường dẫn |
|---|---|
| Đăng nhập / Đăng ký (chọn vai trò) | `/login`, `/register` |
| Giáo viên: các lớp đang dạy | `/teacher` |
| Tạo lớp, chọn chế độ AI | `/teacher/classes/new` |
| Lớp: mã lớp, bài tập, học sinh (email / CSV), tài liệu, lịch sử hỏi AI | `/teacher/classes/[id]` |
| Tạo bài tập có hạn nộp, rubric, đáp án mẫu | `/teacher/classes/[id]/assignments/new` |
| Trạng thái nộp bài, bản nháp AI chấm từng bước, sửa điểm & công bố | `/teacher/assignments/[id]` |
| Học sinh: trang chủ, tham gia lớp bằng mã | `/student` |
| Lớp của học sinh: bài tập, bài giảng | `/student/classes/[id]` |
| Đề bài, nộp bài (gõ / chụp ảnh), trợ lý giải bài (Socratic), kết quả | `/student/assignments/[id]` |
| Đọc bài giảng (PDF / văn bản theo trang) + hỏi AI, bấm thẻ nguồn nhảy đúng trang | `/student/documents/[id]?page=X` |

Token đăng nhập lưu trong `localStorage`; quyền thật luôn được kiểm tra ở backend.

## Ghi chú kỹ thuật
- Chat đọc stream SSE bằng `fetch` (cần header Authorization) — `src/lib/sse.ts`.
- Câu trả lời AI render Markdown + KaTeX; thẻ `[Nguồn: …]` chỉ bấm được khi backend xác nhận nguồn có thật — `src/components/Answer.tsx`.
- `next.config.mjs` bật `output: "standalone"` cho Docker và tắt module `canvas` của pdfjs.
