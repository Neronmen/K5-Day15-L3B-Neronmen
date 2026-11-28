# Rà soát Issue của Thắng ngày 27/11/2026

Main đã pull `4d1f81cacbe21e6a94cb4330829bc4352f20a249`, sau khi merge PR #46 bằng quyền write thông thường. PR không conflict, check GitHub success, main không có protection/rules đang áp dụng. Không force push, không bypass. PR #39 giữ nguyên.

## Đối chiếu acceptance criteria

Đã duyệt toàn bộ danh sách Issue qua GitHub API, gồm cả đã đóng. Các Issue riêng của Thắng có assignee `thangdktd`; Issue #20 là việc chung, chỉ ghi tiến độ của Thắng và giữ mở.

| Issue | Acceptance và bằng chứng trên main | Kết luận |
|---|---|---|
| #7, T-01 | 16 trang logic, 13 bài, 10 bài lớp 10A1 còn hạn, 2 đã hết hạn, 1 lớp khác. DATA_CARD có nguồn/biên soạn; test_data kiểm schema, nghiệm và quyền riêng tư | Đã đóng completed từ trước; giữ nguyên |
| #8, T-02 | check_leak có decimal, fraction, tiếng Việt, LaTeX; 28 test gồm ca không lộ | Đã đóng completed từ trước; giữ nguyên |
| #9, T-03 | 4 metric có định nghĩa, mẫu số, missing data, threshold; Khoa duyệt 18:07, commit ae5bc562866a218c7b96e2da75fe204002cf16db; 3 test metric đạt | Đủ acceptance, đóng completed |
| #16, T-04 | Builder đã merge, kiểm đúng dải/schema/ID trùng; hiện đủ 30 câu, 10/30 nguồn thật; builder --check và run.py check không cảnh báo | Đủ acceptance, đóng completed |
| #17, T-05 | B14–B21 đúng 8 câu, 4 kho; đủ sai dấu -b, quên 2a, Delta, số nghiệm và bước đúng; 10 test toán học/schema. B16/BT09/R24 đã merge qua #45 | Đủ acceptance, đóng completed |
| #18, T-06 | Grader chỉ tạo gợi ý nháp, không ghi đè pass/output; 33 test. Công cụ đã merge | Đã đóng completed từ trước; đối chiếu output thật còn chờ |
| #26, T-07 | Cần hai lượt thật, ít nhất 3 lỗi có input/output/nguyên nhân và người thứ hai chấm 5 output khớp ít nhất 4/5 | Giữ mở; thiếu run/trace, human grades và người chấm độc lập |
| #27, H-05 | Phân tích Q5 26 phiếu, 3 persona, 3 quy mô, ít nhất 2 giá model có URL/ngày xem; đã đo 50 phiên gpt-6-luna, 45 model calls, 84621/10106 token, 0 lỗi kỹ thuật | Đã thực hiện acceptance trong PR mới, giữ mở chờ review/merge H-05; USD/task thành công còn chờ human rate |
| #20, việc chung | Thắng chưa bàn giao phỏng vấn P3 có bằng chứng | Giữ mở; không tính khảo sát R24 là phỏng vấn và không đóng việc thành viên khác |

Không mở lại #7/#8/#18 để làm lại công việc đã hoàn tất. Không xóa Issue hoặc thay đổi Issue riêng của Khoa, Ninh, Nhài. Comment bằng chứng gắn commit, đường dẫn và lệnh kiểm; cập nhật trạng thái API theo `state_reason=completed` cho đúng ba Issue đã đủ acceptance.

## Khóa input trước evaluation

[Manifest](../eval/frozen-inputs-20261127.json) lưu SHA256 của benchmark và metric đã duyệt từ main trên. Dùng `python eval/verify_frozen_inputs.py` trước và sau mỗi lượt. Hash LF là byte Git chuẩn; manifest cũng giữ raw checkout hash để phân biệt CRLF Windows. Đây là lock mới cho lượt sắp chạy, không xác nhận provenance của run lịch sử.

| File | SHA256 với LF |
|---|---|
| eval/benchmark.csv | 2563f387ff9ca6d4135ffe3a2660277a8ded57310d287e93ea6f10669dc326aa |
| eval/metric_spec.yaml | 8fd4261d2da65a149627b770b43f4ee580ad20fe093d5437699dbe6eb51d8d76 |

Benchmark có 30 ID duy nhất, 7 câu khảo sát + 3 review = 10/30 = 33,33% nguồn thật. B16 là BT09/R24, B22 là BT06/R26. Không sửa benchmark, metric hoặc CSV thành viên. Probe checksum sai dùng manifest tạm trong bộ nhớ và bị từ chối, không thay input thật.

## Output thật và H-05

Đã kiểm các nhánh origin đã fetch, mọi worktree đã đăng ký, GitHub Actions artifacts, Releases và body/comment các Issue bàn giao #12/#14/#21/#24/#26/#27. Trước lượt simulation mới, không thấy run-N.csv, manifest/trace evaluation thật phù hợp để chạy grader hoặc so sánh hai lượt; chỉ có simulate-mock cũ trong worktree H-05. Mock giữ nguyên, không dùng cho CP3/CP4. CSV/trace simulation mới dùng riêng cho H-05, không thay evaluation đã chấm. Không kết luận nhóm chưa chạy ở máy khác.

Phần H-05 kế thừa file hoàn chỉnh từ worktree cũ tại 85e0678, không thay worktree đó. Survey main khớp nguyên byte Git và mọi số phân tích cũ. Xem [cost-estimate](../cost/cost-estimate.md) cho giả định, giá, các ô pending và lệnh chạy tiếp. Sau khi người giao việc cấu hình credential, đã chạy 10 phiên thử và 50 phiên API thật. Đây là simulation chi phí, chưa phải bộ evaluation/human grading.

T-06 chưa được đối chiếu với raw output thật; không dùng bản redteam tóm tắt làm run. T-07 giữ draft gốc local, không tự tạo run-1/run-2, lỗi minh họa, human grading hoặc đồng thuận người thứ hai.

## K?t qu? th?c hi?n tr?n GitHub

?? comment b?ng ch?ng v? ??ng completed #9, #16, #17. #7, #8, #18 v?n closed/completed t? tr??c; #26, #27 v? vi?c chung #20 gi? m? v?i comment ti?n ??/blocker. [Receipt API](verification/thang-issue-actions-20261127.json) gi? URL comment t?ng Issue. PR #47 ?? Ready for review, ch?a merge.

Ki?m cu?i: 125/125 unittest, builder/check, CLI SHA256, diff-check v? ??i chi?u token CSV/trace ??u ??t. To?n l??t 50 c? 45 model calls, 84621/10106 token; kh?ng c? API key trong file tracked. Raw CSV/trace/summary v? snapshot ???c b?o to?n byte qua .gitattributes; kh?ng s?a artifact ?? ch?y ?? x? l? CRLF.
