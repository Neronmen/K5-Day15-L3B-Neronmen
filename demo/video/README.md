# Video demo — cách tạo (chạy lại được)

Bản nộp: **v2 (61 giây)** = `capture2.py` + `make_video2.py` — cả phía giáo viên (đăng tài liệu, giao bài, Trợ lý AI, AI chấm nháp, gắn cờ) và học sinh (chỉ bước sai, trích trang, 3 đòn lừa bị chặn, giải sau hạn). Bản 1 (43 giây) = `capture.py` + `make_video.py`.

Video nộp CP3 được dựng **từ web thật + AI thật**, không dựng cảnh giả:

1. `capture.py`: Playwright điều khiển Chrome trên web MinutesStudy chạy local (`app/`, DB sạch, lớp nạp bằng `demo/seed_demo.py`), gõ các câu trong `demo/cau-mau.txt` và chờ **DeepSeek thật** trả lời, rồi chụp 9 cảnh Full HD. Câu trả lời trong video là output thật của lõi `codebase/`, không chỉnh sửa.
2. `make_video.py`: ghép ảnh với zoom nhẹ, chuyển cảnh, phụ đề và giọng đọc tiếng Việt (edge-tts, giọng `vi-VN-HoaiMyNeural`), xuất MP4 1920×1080.

Số liệu ở màn kết lấy từ `eval/report.md` (lượt 1 `run-1@20261128-072817`). Công cụ: Claude Code viết hai script này, nhóm duyệt video trước khi nộp (ghi ở `docs/ai-usage.md`).
