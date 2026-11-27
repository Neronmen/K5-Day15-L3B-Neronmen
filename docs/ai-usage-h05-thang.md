# AI usage H-05 và rà Issue, ngày 27/11/2026

## Phiên tiếp tục theo main 4d1f81c

Codex kiểm quyền, diff, CI và protection rồi merge PR #46 theo yêu cầu. Kế thừa H-05 tại 85e0678, chạy lại phân tích Q5 trên main, xác minh giá ít nhất hai model từ nguồn chính thức và bổ sung OpenAI theo lựa chọn người giao việc. Không tạo dữ liệu khảo sát, token, phỏng vấn hoặc human grading. Người giao việc đã cấu hình key/model local; Codex sửa adapter max_completion_tokens sau HTTP 400, kiểm failing-before/passing-after và chạy 10 phiên thử + 50 phiên thật. Không thay prompt/chính sách/benchmark/metric; token lấy từ usage, các phần quality grading vẫn pending.

Codex lưu manifest SHA256 benchmark/metric và viết CLI kiểm hash, kiểm cả ca hash sai mà không sửa input thật. Rà toàn bộ Issue được giao cho Thắng, đối chiếu acceptance với mã đã merge và test; chỉ đóng #9/#16/#17 đã đủ điều kiện, cập nhật bằng chứng và blocker trên Issue được phép. Không sửa PR #39, metric, benchmark hoặc CSV thành viên.

Chưa tìm thấy raw evaluation thật trong nhánh/worktree/Actions/Releases đã kiểm nên không chạy grader trên dữ liệu tự tạo hoặc hoàn tất T-07. Draft gốc, worktree H-05 cũ và artifact mock được giữ nguyên. Thắng cần đọc và giải thích giả định; Khoa review PR bàn giao.

## Phiên H-05 trước, giữ làm lịch sử

# AI usage bổ sung: H-05 và T-08, ngày 27/11/2026

Codex đọc Issue27, các ticket liên quan, PR39 và snapshot survey ẩn danh của Nhài. Hỗ trợ viết script tổng hợp Q5, tám test bảo toàn mẫu số/nhóm0/dữ liệu thiếu, YAML persona, bảng giả định và hồ sơ chi phí. Giá được đọc từ provider chính thức; các source và ngày được lưu. Không tạo survey response, người được phỏng vấn hoặc dữ liệu P3.

Codex chạy 122 unittest, smoke/check và lượt simulate --try tách biệt với fake. Artifact mock/token0 được giữ và đánh dấu không phải kết quả chi phí thật; không gọi API trả phí, không chạy50 phiên chính thức và không chấm human. Việc không có key hoặc output thật được ghi như blocker. Không dùng số token mẫu hoặc tỷ lệ đạt mặc định để điền giá/task.

Nhánh thang bị xung đột namespace với thang/T-*, nên dùng nhánh tạm thang-h05-t08 mà không xóa nhánh cũ. Thắng cần tự đọc, giải thích và xác nhận số liệu/giả định trước khi nộp. Đây là khai báo bổ sung cho docs/ai-usage.md, giữ nguyên tài liệu và draft ở PR39 để tránh nhập lại thay đổi đã bàn giao.

## Lượt API thật sau khi có cấu hình

Codex dùng key từ .env local qua process environment, không lưu secret trong file bàn giao. Probe B16 trả HTTP 400 với max_tokens; test adapter tái hiện lỗi trước sửa và đạt sau sửa. Đổi đúng tham số ở ai.py, giữ @model_call và usage API, không đổi prompt hoặc tutor policy. 10 phiên thử + 50 phiên chính thức dùng gpt-6-luna; 50 phiên có 45 calls và 84621/10106 token, trace đối chiếu khớp CSV. Chi phí báo là token-price reference estimate, chưa phải account invoice. Không tự chấm pass hoặc kết luận chất lượng từ không có lỗi kỹ thuật.
