# Khai báo dùng AI

README của nhóm có mục "Dùng AI vào việc gì" (2–3 dòng, bắt buộc). Ghi chi tiết vào bảng dưới đây.

> Luật của đề: dùng AI để làm bài thoải mái, nhưng **ai không giải thích được phần có tên mình thì phần đó nhận 0 điểm**. Khai thiếu không bị trừ; giấu mới bị.

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code bản chạy thử | Codex, phiên 27/11/2026 | Hỗ trợ T-02 check_leak, T-04 builder, T-06 công cụ chấm nháp và unittest; tích hợp main mới của Khoa | 108 test đạt tại 950815a; review bằng tác nhân độc lập tìm lỗi chuỗi đẳng thức và ±, đã sửa và kiểm lại qua checker/agent/grader; Khoa và Thắng chưa xác nhận review tay | Nguyễn Hồng Thắng |
| Prompt / thiết kế lời gọi mô hình | | | | |
| Đào data (viết script đếm, gợi ý nhãn) | Claude Code (Claude Opus 5.5) | Viết `evidence/count_reviews.py` (đếm nhãn review) và `evidence/survey/analyze_survey.py` (ẩn danh + đếm khảo sát theo luật đọc ở `questions.md`); chạy thử trên dữ liệu giả ngoài repo. Viết `evidence/fetch_reviews.py` (Nhài chạy, lấy 150 review thật). **Gợi ý nhãn** cho 149 review (cột `nhan_ai`, 11 dòng ghi "CẦN DUYỆT"). **Không** tạo review hay câu trả lời khảo sát | Nhài duyệt từng dòng cột `nhan`; khớp với nhãn AI: 144/149, Nhài đổi 5 dòng (4, 15, 20, 69, 102), lý do ở cột `ghi_chu` | Nhài |
| Rà câu hỏi phỏng vấn / khảo sát | Claude Code (Claude Opus 5.5) | Chuyển nguyên văn `evidence/survey/questions.md` thành Apps Script `create_form.gs` tạo Google Form (ẩn danh, không thu email); không đổi câu hỏi | Nhài chạy script, mở form kiểm đủ 9 câu | Nhài |
| Viết câu thử (benchmark) | Codex, phiên 27/11/2026 | Hỗ trợ soạn B14–B21, expected và test kiểm toán học | Đúng 8 câu, 4 kho, source tu_viet có ghi Codex/synthetic; kiểm bằng phân số và phép thế; Thắng chưa xác nhận đọc tay | Nguyễn Hồng Thắng |
| Viết câu thử (benchmark) | Claude Code (Claude Opus 5.5) | Soạn B22 từ phỏng vấn P1 và B23–B25 từ review thật (dòng 81, 52, 38 của `reviews_labeled.csv`), viết lại thành tin nhắn học sinh | Nhài duyệt từng câu trước khi ghi; `source` ghi rõ dòng gốc và "viết lại thành tin nhắn học sinh" | Nhài |
| Sinh data `synthetic` (nếu có) | Codex, phiên 27/11/2026 | Tự soạn 15 trang logic chương Toán 10, 1 trang lớp khác và 13 bài; không sao chép SGK | Không dùng sinh ngẫu nhiên nên không có seed; 10 test dữ liệu kiểm schema, liên kết, thời hạn, toàn bộ nghiệm; chưa có số dòng được người kiểm tay xác nhận | Nguyễn Hồng Thắng |
| Chấm cột `pass` bằng LLM (nếu có) | | | Kiểm tra thủ công __ câu thử, khớp __/__ | |
| Slide, văn bản | Codex, phiên 27/11/2026 | Hỗ trợ metric đề xuất, hướng dẫn chấm, bàn giao; chuẩn bị bản nháp reflection và báo cáo chờ dữ liệu thật | Ngưỡng chờ Khoa duyệt trước CP2; reflection cần Thắng tự hoàn thiện; không tạo slide hoặc số liệu eval thật | Nguyễn Hồng Thắng |

Phần trên chỉ khai báo việc AI hỗ trợ Thắng trong phiên này. Các ô còn trống thuộc công việc chưa được khai báo ở đây, không có nghĩa là thành viên khác có hoặc không dùng AI. Công cụ chấm T-06 không gọi LLM và không tự điền pass. Không có run-1/run-2 hay phỏng vấn thật do phiên này tạo ra.

**Không dùng AI để:** tạo người được phỏng vấn, trích dẫn, câu trả lời khảo sát; sửa kết quả các lượt đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/`).

## Rà soát CP2 của Thắng, ngày 27/11/2026

Codex đọc trạng thái GitHub, dependency, commit/file, CI/review và chạy kiểm chứng trên main 0e96a99 trong worktree riêng. Đã xác minh cả sáu head có trong main, 108 unittest đạt; smoke dùng MODEL_PROVIDER=fake, probe dùng stub synthetic, không gọi model thật trong phiên rà soát. Ghi lại hai điểm hợp đồng chấm cần Khoa/Ninh thống nhất, không sửa agent, CSV, metric hoặc ngưỡng. Chỉ bổ sung tài liệu bàn giao và gợi ý xử lý PR34 dư; không merge main hay đóng Issue.

Ba file nháp T-07 có backup byte-for-byte trước fetch; cập nhật local được thêm vào mà không xóa bản gốc. Không tạo output eval hay human grading/phỏng vấn giả. Dữ liệu kiểm thử synthetic không phải bằng chứng người dùng. Các dòng khai báo của thành viên khác được giữ nguyên. Hướng dẫn và biên nhận: docs/cp2-review-thang.md, docs/verification/thang-cp2-20261127.json.

### Cập nhật cuối theo main cce4e72

Trong cùng phiên rà soát, upstream bổ sung code app/core, 5 test của Khoa và 4 câu có nhãn nguồn thật của Nhài. Codex merge upstream vào nhánh review riêng, không merge main; kiểm113/113 unittest và các probe bằng fake/stub trên runtime/data/test giống main cce4e72. Benchmark hiện25 câu, 4/25 nguồn thật theo nhãn và có điểm đối chiếu P1/review; không tạo interview, nguồn mới hoặc đổi nhãn. Không sửa code/metric/CSV. Các khai báo Nhài và thành viên khác được giữ từ main mới; snapshot0e96a99 phía trên là lịch sử lượt đầu.

### Chốt kiểm chứng tại main1711525

Khoa đã sửa hợp đồng nguồn và đồng bộ số đếm trong lúc review. Codex kiểm lại114/114 test trên runtime/data/test giống main1711525; probe thẻ nhiều nguồn PASS, không còn ghi đó là blocker. Giữ các lượt0e96a99/cce4e72 như lịch sử. Chỉ cập nhật docs, không đổi runtime/metric/CSV, không gọi model thật hoặc tạo human grading/phỏng vấn. PR38 lượt đầu đã được tích hợp bởi Khoa; phần cập nhật cuối được bàn giao riêng bằng diff tài liệu.

## Tiếp tục T-03, T-04, T-06 và draft T-07 theo main 12250ae

Codex đối chiếu commit duyệt metric ae5bc56 và các Issue/PR mới; kiểm benchmark main cùng candidate CSV Nhài tại b35509a, đối chiếu năm đoạn nguồn khảo sát. Chỉ đọc dữ liệu khảo sát ẩn danh, không tạo câu trả lời, phỏng vấn hoặc gán lại source. Không sửa metric, expected, agent hay dữ liệu của tác giả khác.

Codex chạy smoke fake, check, 114 unittest, diff-check và các probe fake/stub; builder từ chối đúng candidate 9/30 nguồn thật. Đã ghi fingerprint SHA-256 hiện tại, không gán thành provenance của lượt model thật. Không tìm thấy run/trace phù hợp nên không chạy auto grader trên dữ liệu tự tạo, không chấm human hay người thứ hai. T-07 được cập nhật local bằng số đã kiểm chứng; reflection chỉ bổ sung hồ sơ công việc, Thắng còn phải tự xác nhận. Không gọi API model thật, không chạy mô phỏng H-05, không merge main hoặc đóng Issue.
