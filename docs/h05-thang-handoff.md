# Bàn giao H-05, rà Issue và khóa evaluation

## Rà soát trước merge PR #47 ngày 27/11/2026

Đã kiểm lại acceptance gốc Issue #27: ba persona từ Q5, 50 phiên API thật, ba kịch bản chi phí và giá ít nhất hai model có URL/ngày xem đều đủ. Đối chiếu lại CSV/trace khớp 84621 input/10106 output, 45 calls, không lỗi kỹ thuật; 125 unittest, builder/check, diff-check và SHA256 benchmark/metric đạt. TICKETS đánh dấu H-05 đã thực hiện đầy đủ acceptance. USD/task thành công vẫn pending human pass rate và không được thay bằng tỷ lệ không lỗi kỹ thuật. Các đoạn giữ trạng thái chờ review bên dưới ghi lịch sử lúc mở PR; Issue #27 chỉ đóng completed sau khi PR #47 merge.

PR #34 là PR dư: head f888a15 và mọi commit đã có trong main; đóng kèm bằng chứng, không merge lại hoặc ghi đè B16/BT09/R24 đã được cập nhật qua T-08. PR #39 và draft T-07 giữ nguyên.

Cập nhật ngày 27/11/2026 trên main 4d1f81c sau merge PR #46. Nhánh thang/H-05-audit kế thừa nội dung H-05 từ worktree cũ tại 85e0678; worktree cũ và artifact mock giữ nguyên. Không nhập draft T-07 ở workspace gốc. PR #39 đã merged từ trước, không chỉnh sửa.

Phân tích Q5 hiện tại khớp snapshot cũ: 26 phiếu hợp lệ, phân bố 3/4/2/7/10, persona 7/2/17. Cấu hình có 50 phiên seed 42, mỗi phiên một lượt độc lập; giả định và độ nhạy trong [cost-estimate](../cost/cost-estimate.md). Giá được đọc lại từ OpenAI, DeepSeek và Gemini ngày 27/11/2026. Provider người giao việc chọn là OpenAI, đã cấu hình gpt-6-luna local. Adapter cần sửa tương thích max_completion_tokens; test hồi quy đạt, sau đó 50 phiên thật hoàn tất. Token/giá và ba quy mô đã có báo cáo, USD/task thành công vẫn chờ human rate.

Benchmark và metric giữ nguyên, đã lưu SHA256 trước evaluation. Chạy `python eval/verify_frozen_inputs.py` trước và sau mỗi lượt thật. Lock và kết quả audit có ở [hồ sơ Issue](thang-issue-audit-20261127.md).

Issue #9/#16/#17 đủ acceptance trên mã đã merge và được xử lý completed theo yêu cầu. #7/#8/#18 giữ closed/completed từ trước. #27 đã có đủ phần persona/50 phiên/ba quy mô/giá model trong PR này, giữ mở chờ review và merge vào main. USD/task thành công là phần báo cáo còn phụ thuộc human rate. #26 và việc chung #20 giữ mở vì thiếu evaluation/human grading hoặc phỏng vấn. Không đóng Issue của thành viên khác hoặc xóa lịch sử.

Không tìm thấy raw run/trace evaluation thật của nhóm trong các nguồn đã kiểm trước simulation, nên chưa chạy auto-grade thực tế, so sánh T-07 hoặc chi phí/task thành công. Simulation chi phí mới có CSV/trace riêng và không thay run evaluation đã chấm. Khoa/Ninh cần bàn giao output, config và manifest cùng hash; người thật xác nhận pass và chấm độc lập. P3 vẫn cần phỏng vấn thật; không còn là blocker của benchmark 10/30.

Nhánh dùng tiền tố thang/ do tên thang xung đột namespace với các nhánh hiện có. Không xóa nhánh, force push, sửa framework hoặc đổi metric đã duyệt. AI usage bổ sung ở [ai-usage-h05-thang.md](ai-usage-h05-thang.md), kiểm chứng hiện tại ở docs/verification/thang-h05-audit-20261127.json. Receipt cost/h05-verification-20261127.json là lịch sử lượt mock cũ, không phải kết quả 50 phiên thật.
