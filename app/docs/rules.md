# Bộ Rules của hệ thống & AI Agent

Đây là các luật **bắt buộc**. Mỗi luật ghi rõ nơi thực thi trong code.

## 1. Dữ liệu & Kiến thức (Grounding)

### Rule 1 — Bám sát bài giảng, không bịa
- Agent chỉ lấy kiến thức từ tài liệu giáo viên đã đăng (bài giảng, slide, giáo án, sách). Đây là nguồn chân lý.
- Mỗi ý trả lời phải trích dẫn nguồn: tên bài giảng / tài liệu và vị trí (trang, mục).
- Giáo viên chọn chế độ AI cho từng lớp: **Khoá cứng** (không dùng kiến thức ngoài) hoặc **Mở rộng** (được dùng, nhưng phải gắn nhãn `[Kiến thức mở rộng ngoài giáo trình]` **và ghi rõ nguồn** như tên sách, URL).
- Thẻ nguồn dạng `[Nguồn: Tên_file - Trang X]`, bấm vào nhảy đúng trang.
- Không tìm thấy nguồn thì nói "Mình không tìm thấy nội dung này trong bài giảng", **tuyệt đối không bịa**.
- Thực thi: `backend/app/agents/prompts.py` (chỉ thị), `backend/app/agents/knowledge.py` (chỉ đưa đoạn tài liệu đã truy xuất vào ngữ cảnh, kiểm tra câu trả lời có trích dẫn).

### Rule 2 — Phân tách dữ liệu giữa các lớp (Multi-tenant Isolation)
- Dữ liệu vector (RAG), lịch sử chat, bài tập của Lớp A không bao giờ lộ sang Lớp B.
- Mọi truy vấn Vector DB bắt buộc kèm bộ lọc `teacher_id`, `class_id`, `subject_id`.
- Thực thi: `backend/app/core/tenancy.py` — hàm truy vấn duy nhất, thiếu bộ lọc là báo lỗi.

## 2. Hành vi Agent (Guardrails)

### Rule 3 — Chế độ Sư phạm (Socratic Guardrail)
Khi user có `role = student` hỏi về bài tập **còn hạn** (`active_assignment`), Agent không đưa đáp án cuối cùng, chỉ được:
1. Kiểm tra bước làm hiện tại của học sinh.
2. Chỉ ra lỗ hổng tư duy / công thức sai.
3. Gợi ý bước tiếp theo.

Sau hạn nộp, Agent được đưa đáp án và lời giải. Đáp án mẫu của giáo viên chỉ được đưa vào ngữ cảnh AI sau hạn.
- Thực thi: `backend/app/agents/policy.py` (tính chế độ bằng giờ server).

### Rule 4 — Giáo viên duyệt điểm (Human-in-the-Loop)
- Điểm do Grading Agent chấm luôn ở trạng thái `pending_review`.
- Không bao giờ công bố điểm cho học sinh khi giáo viên chưa xác nhận, trừ khi giáo viên bật tự động duyệt cho bài trắc nghiệm.
- Thực thi: `backend/app/models.py` (`Grade.status`), `backend/app/grading/service.py`.

## 3. Nghiệp vụ LMS

### Rule 5 — Khoá bài nộp & Phiên bản đề
- Khi học sinh nộp bài hoặc hết hạn, bài làm bị khoá (read-only).
- Giáo viên sửa đề sau khi đã giao → tạo phiên bản mới (`v2`), không ghi đè. Bài nộp luôn gắn với phiên bản đề mà học sinh đã làm.
- Thực thi: `backend/app/models.py` (`AssignmentVersion`, `Submission.locked`).

## 4. Chống gian lận
- System prompt cố định ở backend, input học sinh luôn nằm trong vai `user`, không bao giờ được ghép vào system prompt.
- Lưu toàn bộ hội thoại học sinh–AI để giáo viên xem lại.
- Thực thi: `backend/app/agents/tutor.py`, bảng `ChatMessage`.
