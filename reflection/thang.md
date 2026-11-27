# Reflection — Nguyễn Hồng Thắng

> Bản nháp theo `TEMPLATE.md`, ngày 27/11/2026. Thắng cần tự đọc, sửa và xác nhận trước khi nộp 23:59 ngày 28/11/2026. Chưa có phản tư cá nhân hay kết quả eval thật được xác nhận.

1. Vai trò + phần mình làm (trỏ tới file / commit):
   Vai trò được giao là dữ liệu, chốt chặn và công cụ chấm.
   Dữ liệu ở `data/`, kiểm leak ở `codebase/tools.py`, builder và grader ở `eval/`.
   Các commit triển khai gồm `460572f`, `be91602`, `a33d975`, `326afa3`, `f888a15`, `360f4e6`.
   Trạng thái duyệt, dependency và PR được ghi trong `docs/thang-handoff.md`.

2. AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):
   Codex hỗ trợ tự soạn dữ liệu synthetic, tám câu thử, mã kiểm tra và tài liệu.
   Test được dùng để kiểm lại nghiệm, ngữ cảnh số và việc bảo toàn output/điểm người chấm.
   Toàn bộ phạm vi AI hỗ trợ được khai tại `docs/ai-usage.md`; người phụ trách chưa xác nhận review tay.
   Thắng bổ sung nhận xét cá nhân về phần AI làm chưa phù hợp sau khi tự chạy và giải thích code.

3. Một câu thử trượt của nhóm và mình học được gì từ nó:
   Pending. Chưa có hai lượt model thật để chọn một câu trượt của nhóm.
   Kiểm tra v0 cho thấy `x=20` bị so chuỗi nhầm thành `x=2`, còn `x1=2` có thể bị bỏ sót.
   Đây là lỗi unit test của starter, không phải kết quả benchmark CP3/CP4 hay phản hồi người dùng.
   Sau lượt thật, Thắng tự điền case ID, input/output/expected, nguyên nhân và điều mình rút ra.
