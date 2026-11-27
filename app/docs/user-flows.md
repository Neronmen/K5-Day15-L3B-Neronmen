# User Flow

## 1. Giáo viên

### 1.1 Khởi tạo & quản lý lớp
- Đăng nhập → **Dashboard** các lớp đang dạy.
- **Tạo lớp mới**: tên lớp (vd *Toán 10A1 - Học kỳ 1*), môn học, chế độ AI:
  - **Khoá cứng**: AI chỉ dùng bài giảng.
  - **Mở rộng có trích nguồn**: được dùng kiến thức ngoài, phải gắn nhãn và ghi nguồn.
- **Thêm học sinh**: nhập email / mã học sinh, gửi **Class Code**, hoặc import Excel/CSV.

### 1.2 Nạp tri thức
- **Tài liệu bài giảng** → upload PDF / Word / Slide.
- Chạy ngầm: bóc tách → chia đoạn **kèm số trang** → lưu Vector DB gắn `class_id`.
- Giáo viên nhận thông báo khi tài liệu sẵn sàng cho AI.

### 1.3 Giao bài & duyệt điểm
- Tạo bài tập: tự nhập, tải file đề, hoặc AI sinh đề từ bài giảng → đặt **deadline** và **rubric**.
- Theo dõi realtime: **Đã nộp / Chưa nộp / Nộp muộn**.
- Mở danh sách bài AI chấm nháp → xem nhận xét từng bước → sửa điểm → **Duyệt & Công bố**.

## 2. Học sinh

### 2.1 Tham gia lớp
- Đăng nhập → thấy các lớp đã được add (hoặc nhập Class Code).
- Trang chủ: bài giảng và bài tập sắp đến hạn.

### 2.2 Học & hỏi Knowledge Agent
- Mở bài giảng, chat ở khung bên cạnh.
- AI trả lời theo bài giảng kèm thẻ `[Nguồn: Tên_file - Trang X]`. Bấm thẻ → nhảy đúng trang tài liệu.

### 2.3 Làm bài & hỏi gia sư
- Mở bài tập → khung **Trợ lý giải bài** chạy **Socratic Mode**: chỉ gợi ý phương pháp / công thức từ bài giảng, không đưa đáp án cuối.
- Nộp bài: gõ trực tiếp hoặc chụp ảnh vở.
- Ảnh mờ → báo chụp lại ngay → lưu bản nộp → chờ giáo viên duyệt để xem điểm và lời giải.

## 3. Ánh xạ sang hệ thống

| Bước | API (backend/app/main.py) | Trang (frontend) |
|---|---|---|
| Dashboard giáo viên | `GET /teacher/dashboard` | `/teacher` |
| Tạo lớp, chọn chế độ AI | `POST /teacher/classes` | `/teacher/classes/new` |
| Thêm / import học sinh | `POST /teacher/classes/{id}/students[/import]` | `/teacher/classes/[id]/students` |
| Upload tài liệu | `POST /teacher/classes/{id}/documents` → job `ingest_document` | `/teacher/classes/[id]/documents` |
| Tạo bài tập | `POST /teacher/classes/{id}/assignments` | `/teacher/classes/[id]/assignments/new` |
| Trạng thái nộp bài | `GET /teacher/assignments/{id}/submissions` (+ WebSocket) | `/teacher/assignments/[id]` |
| Duyệt điểm | `GET .../grades`, `POST /teacher/grades/{id}/publish` | `/teacher/assignments/[id]/grading` |
| Trang chủ học sinh | `GET /student/home`, `POST /student/join` | `/student` |
| Chat bên bài giảng | `POST /student/documents/{id}/chat` | `/student/documents/[id]?page=X` |
| Trợ lý giải bài | `POST /student/assignments/{id}/chat` | `/student/assignments/[id]` |
| Nộp bài / xem kết quả | `POST .../submit`, `GET .../result` | `/student/assignments/[id]` |
