# Bàn giao CP2 của Thắng, ngày 27/11/2026

Main mới nhất đã kiểm tra: `17115257d4c46f41d3b9299a368908988355ed53`. Runtime/data/test ở worktree04d837f giống hệt main này. Phiên rà soát không merge main, không sửa agent/metric/benchmark và không đóng Issue.

## Trạng thái sáu PR

| PR | Base → head | Trạng thái | Xử lý |
|---|---|---|---|
| #30 | main → thang/T-01 | merged, f11653a | Không cần chuyển Ready hay merge lại |
| #31 | main → thang/T-02 | merged, ea0e327 | Không cần chuyển Ready hay merge lại |
| #32 | main → thang/T-03 | merged, a33d975 | Phê duyệt metric vẫn pending |
| #33 | main → thang/T-04 | merged, 267173c | Builder đã có; chờ benchmark cuối |
| #34 | thang/T-01 → thang/T-05 | open/draft, f888a15 | Đã có trong main qua T-06; PR dư, Khoa xác nhận rồi đóng |
| #35 | main → thang/T-06 | merged, a87ec4d | Dependency đã tích hợp; không replay stack |

Cả sáu head đều là ancestor của main, có0 commit chưa tích hợp. T-01 trước T-05, T-01–T-05 trước T-06 là dependency lịch sử đã giải quyết. PR34 không có conflict với base cũ nhưng không cần merge. Sáu PR không có review comment, commit status hay check run tại lúc đọc; pending với count0 không phải CI PASS.

## Kiểm chứng cuối

- python run.py: exit0, smoke fake/token0, không gọi model thật.
- python run.py check: exit0,25 câu B01–B25,8 thuong/13 kho/4 tu_choi,4 metric; còn cảnh báo nguồn thật4/25.
- python -m unittest discover -s tests -v: **114/114 PASS**, gồm6 test guardrail Khoa thêm so với bộ108 ban đầu.
- git diff --check: exit0.
- Builder --check: exit1 đúng dự kiến, thiếu B26–B30; không ghi đè benchmark.
- 8 probe chuỗi đẳng thức/±/phân số/LaTeX đều bị chặn, agent retry rồi SAFE_HINT;7 ca số trung gian/biên không bị báo nhầm;4 ca policy trước/đúng/sau hạn và teacher đúng. Không sửa agent Khoa.
- Lỗi thẻ nhiều nguồn đã được upstream sửa: citations xuất hai thẻ riêng, grader grounding PASS trong probe synthetic. Đây là test hợp đồng, không phải điểm model thật. B13 đã được upstream thống nhất nhãn.

Khoa sẵn B01–B06, Ninh sẵn B07–B13, Thắng sẵn B14–B21 (test toán/data tương thích), Nhài mới sẵn B22–B25. Thiếu B26–B30. Bốn nhãn nguồn thật hiện có gồm1 người dùng P1 và3 data_that trỏ dòng review81/52/38; đã đối chiếu nguồn trong repo, không tự đổi nhãn. P1 còn thiếu ngày giờ/hình thức để Nhài điền từ thực tế. Mục tiêu cuối>=10/30 vẫn chưa đạt; ngay cả khi5 câu còn lại đều thật, vẫn cần ít nhất1 câu có bằng chứng thật ở dải khác.

## Mức sẵn sàng CP2 và blocker

Code, data card,25 câu,4 định nghĩa metric và kiểm thử đã sẵn sàng review CP2. Chưa tuyên bố CP2 đã hoàn tất hoặc chuẩn đã được duyệt.

1. Metric trên main là leak0%, decision_accuracy>=80%, error_pinpoint>=70%, grounding>=80% do Khoa thay ở00327f8; approval vẫn pending, spec§7 còn nháp. Phiên này không đổi ngưỡng. Khoa cần xác nhận trước19:15 ngày27/11/2026 UTC+7, khóa trước19:30.
2. B08/B12 còn khác tập nhãn giữa expected và pass_criterion. Khoa/Ninh cần thống nhất trước khi chấm; phiên này không sửa câu thử hay expected.
3. Benchmark thiếu5 câu và tỷ lệ nguồn thật chưa đủ. Không bù nguồn hoặc số liệu giả.
4. Khoa ghi đã thử DeepSeek B01–B03 ở0d18fe4; chưa có run-N/trace để T-06 đối chiếu. Phiên này chỉ fake/stub, không tạo run-1/run-2 hoặc điểm human.
5. T-07 chờ benchmark hoàn chỉnh, metric chốt, output thật, human error_pinpoint và người thứ hai chấm độc lập5 output (khớp>=4/5). Phỏng vấn riêng của Thắng vẫn chờ; P1 của Nhài không phải phỏng vấn của Thắng.

## Việc Khoa và Thắng cần làm

Khoa xác nhận PR34 dư rồi đóng PR, không cần merge lại hoặc đóng Issue chưa đủ criteria. Duyệt metric, thống nhất B08/B12 với Ninh, điều phối B26–B30 và nguồn thật, chạy eval sau khi khóa snapshot. Spec số đếm đã được upstream đồng bộ25; lỗi nguồn cũng đã sửa nên không giữ hai việc đó như blocker cũ.

Thắng tự đọc và giải thích phần code/data, gửi Khoa xác nhận đúng hạn, phối hợp grader trên output thật khi có; phỏng vấn ít nhất một người thật, ẩn danh và thống nhất mã P với Nhài, tự hoàn thiện reflection. Không để AI đóng vai người chấm độc lập thứ hai.

Workspace gốc vẫn thang/T-07. Ba bản nháp được backup và nối thêm, giữ mọi byte gốc, chưa commit vào PR tài liệu. Hồ sơ chi tiết: docs/cp2-review-thang.md; biên nhận mới: docs/verification/thang-cp2-20261127.json. Các snapshot0e96a99/cce4e72 và biên nhận triển khai950815a được giữ làm lịch sử, không thay bằng số liệu mới.
