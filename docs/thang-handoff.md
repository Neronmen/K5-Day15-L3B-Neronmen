# Bàn giao CP2 của Thắng, ngày 27/11/2026

Main được kiểm tra là `cce4e7212f30a061334448d72e462fcb3b068137`. Khoa đã tích hợp phần triển khai T-01–T-06; phiên rà soát này không merge main, không thay metric/câu thử/code agent và không đóng Issue.

## Sáu PR

| PR | Base → head | Trạng thái hiện tại | Xử lý |
|---|---|---|---|
| #30 | main → thang/T-01 | merged, head f11653a | Không cần chuyển Ready hoặc merge lại |
| #31 | main → thang/T-02 | merged, head ea0e327 | Không cần chuyển Ready hoặc merge lại |
| #32 | main → thang/T-03 | merged, head a33d975 | Metric vẫn chờ Khoa duyệt |
| #33 | main → thang/T-04 | merged, head 267173c | Builder xong; benchmark cuối còn thiếu |
| #34 | thang/T-01 → thang/T-05 | open/draft, head f888a15 | Head đã nằm trong main qua T-06; PR dư, đề nghị Khoa xác nhận rồi đóng |
| #35 | main → thang/T-06 | merged, head a87ec4d | Toàn bộ dependency đã có, không đưa lại stack |

Cả sáu head đều là ancestor của main, mỗi head có 0 commit chưa tích hợp. T-01 trước T-05 và T-01–T-05 trước T-06 là dependency lịch sử, không còn là danh sách merge còn phải làm. Không có review comment hoặc CI check/status nào cho sáu PR ở lúc đọc; không suy CI PASS từ trạng thái pending với count=0.

## Kết quả đã kiểm chứng trên main mới

- `python run.py`: exit 0, fake/token 0 để smoke không gọi API.
- `python run.py check`: exit 0, 25 câu B01–B25, 8 thuong/13 kho/4 tu_choi, 4 metric. Còn cảnh báo nguồn thật 4/25 (1 nguoi_dung, 3 data_that).
- `python -m unittest discover -s tests -v`: 113/113 PASS (thêm 5 test guardrail của Khoa).
- `git diff --check`: exit 0.
- Builder `--check`: exit 1 đúng dự kiến, `nhai.csv` thiếu B26–B30, không ghi đè benchmark.
- Hồi quy bằng stub: 8 ca lộ được chặn và agent trả SAFE_HINT sau retry; 7 ca số trung gian/biên không báo nhầm; 4 ca tutor mode trước/đúng/sau hạn và teacher đúng. Không sửa agent của Khoa.

Khoa có B01–B06, Ninh có B07–B13, Thắng có B14–B21. Nhài đã có B22–B25. Cần thêm 5 câu B26–B30 và tổng ít nhất 10/30 nguồn thật; không tự đổi nhãn synthetic. T-05 đã kiểm tương thích dữ liệu T-01 bằng 10 test riêng trong bộ 108 test.

## Chưa đủ điều kiện chốt

1. Metric trên main do Khoa đổi ở 00327f8 hiện là 0%/80%/70%/80%; approval vẫn pending và spec §7 còn nháp. Phiên này không đổi metric hay ngưỡng. Khoa cần duyệt trước 19:15 ngày 27/11/2026 UTC+7 và khóa chuẩn trước 19:30.
2. Khoa/Ninh cần thống nhất nhãn của B08, B12 (B13 đã được upstream thống nhất): expected và pass_criterion đang cho tập nhãn khác nhau hoặc nhiều nhãn, trong khi grader theo spec yêu cầu nhãn duy nhất.
3. Probe synthetic cho thấy thẻ `[Nguồn: P02 - Trang 2; P03 - Trang 3]` hợp lệ theo citations nhưng grader chưa đọc được nhiều mã trong một thẻ. Không dùng số grounding này làm kết quả chính thức trước khi thống nhất hợp đồng. Xem ví dụ đủ mã và lệnh tái lập trong hồ sơ review.
4. Khoa ghi đã thử DeepSeek B01–B03 ở commit 0d18fe4; chưa có run-N/trace thật để công cụ Thắng kiểm chứng. T-06 còn giới hạn chưa đối chiếu output thật; phiên này chỉ chạy fake/stub.
5. Benchmark đủ bộ, nguồn thật đủ tỷ lệ, output thật, human error_pinpoint và người thứ hai chấm độc lập 5 output đều còn chờ. T-07/Issue26 và phỏng vấn Issue20 không được báo hoàn thành.

## Việc cần thực hiện

Khoa xác nhận PR34 dư, duyệt metric và hợp đồng chấm, điều phối dữ liệu thật rồi chạy eval trên cùng snapshot. Không merge lại các PR đã có. Nhài hoàn thiện B26–B30 và ngày giờ/hình thức còn thiếu ở P1 từ thực tế; nhóm cần ít nhất một câu nguồn thật ngoài dải Nhài.

Thắng đọc lại và giải thích phần của mình, gửi Khoa xác nhận trước 19:15, phối hợp sửa hợp đồng chấm trong ticket hiện có sau khi thống nhất, thực hiện phỏng vấn thật và thống nhất mã P với Nhài. Reflection vẫn là bản nháp để Thắng tự hoàn thiện. AI không làm người chấm độc lập thứ hai.

Chi tiết từng PR, commit/file, CI, dependency và input/output tái lập nằm ở `docs/cp2-review-thang.md`; biên nhận mới ở `docs/verification/thang-cp2-20261127.json`. Spec §7 còn ghi21 câu dù CSV hiện25, cần Khoa cập nhật số đếm mà không tự đổi ngưỡng. Runtime ở worktree4bbb10c đã đối chiếu giống hệt main cce4e72; khác biệt chỉ ở tài liệu. Biên nhận triển khai cũ tại950815a vẫn giữ trong `docs/verification/thang-20261127.json`, không thay bằng kết quả mới. Workspace gốc giữ branch T-07 và nội dung chưa commit; kiểm tra tích hợp chạy ở worktree riêng.
