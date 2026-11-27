# Khai báo dùng AI

README của nhóm có mục "Dùng AI vào việc gì" (2–3 dòng, bắt buộc). Ghi chi tiết vào bảng dưới đây.

> Luật của đề: dùng AI để làm bài thoải mái, nhưng **ai không giải thích được phần có tên mình thì phần đó nhận 0 điểm**. Khai thiếu không bị trừ; giấu mới bị.

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code bản chạy thử | | | | |
| Prompt / thiết kế lời gọi mô hình | | | | |
| Đào data (viết script đếm, gợi ý nhãn) | Claude Code (Claude Opus 5.5) | Viết `evidence/count_reviews.py` (đếm nhãn review) và `evidence/survey/analyze_survey.py` (ẩn danh + đếm khảo sát theo luật đọc ở `questions.md`); chạy thử trên dữ liệu giả ngoài repo. **Không** gắn nhãn review, **không** tạo câu trả lời | Nhãn review gắn tay toàn bộ. Kiểm tay __ dòng, khớp __ | Nhài |
| Rà câu hỏi phỏng vấn / khảo sát | Claude Code (Claude Opus 5.5) | Chuyển nguyên văn `evidence/survey/questions.md` thành Apps Script `create_form.gs` tạo Google Form (ẩn danh, không thu email); không đổi câu hỏi | Nhài chạy script, mở form kiểm đủ 9 câu | Nhài |
| Viết câu thử (benchmark) | | | Mỗi câu thử có `source`; câu thử AI viết được ghi rõ | |
| Sinh data `synthetic` (nếu có) | | | Seed __ · kiểm tay __ dòng | |
| Chấm cột `pass` bằng LLM (nếu có) | | | Kiểm tra thủ công __ câu thử, khớp __/__ | |
| Slide, văn bản | | | | |

**Không dùng AI để:** tạo người được phỏng vấn, trích dẫn, câu trả lời khảo sát; sửa kết quả các lượt đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/`).
