# Bàn giao phần Thắng, ngày 27/11/2026

## Trạng thái từng ticket

PASS dưới đây là phần triển khai và kiểm thử đã kiểm chứng, vẫn chờ Khoa review/merge. PARTIAL có code hoặc tài liệu dùng được nhưng còn điều kiện chưa hoàn tất. Không có kết quả model thật hoặc phỏng vấn do phiên này tạo ra.

| Ticket / Issue | Trạng thái | Test thật đã chạy | Commit phần việc | Draft PR | Dependency và phần còn chờ |
|---|---|---|---|---|---|
| T-01 / #7 | PASS | 10/10 | `460572f`, bổ sung `f11653a` | [#30](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/30) | Không phụ thuộc; Thắng đọc lại nội dung, Khoa review |
| T-02 / #8 | PASS | 28/28; tích hợp kiểm mọi đáp án của 13 bài | `be91602`, sửa review `d102942`, `ea0e327` | [#31](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/31) | Không phụ thuộc khi chạy riêng; Khoa review giới hạn bộ chặn |
| T-03 / #9 | PARTIAL | 3/3 | `a33d975` | [#32](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/32) | Chờ Khoa duyệt định nghĩa/ngưỡng trước 19:15 ngày 27/11/2026 UTC+7 |
| T-04 / #16 | PARTIAL | 24/24 | `326afa3`, cập nhật contract `267173c` | [#33](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/33) | Script xong; benchmark cuối chờ ba file tác giả khác và đủ nguồn thật |
| T-05 / #17 | PASS | 10/10 riêng, 20/20 cùng dữ liệu T-01 | `f888a15` | [#34](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/34) | Phụ thuộc #30; PR base `thang/T-01` |
| T-06 / #18 | PARTIAL | 33/33 riêng; 108/108 bản tích hợp | `360f4e6`, hồi quy `655fdd6`, `950815a` | [#35](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/35) | Code và fixture xong; phụ thuộc #30–#34, chờ đối chiếu output model thật và người chấm |
| T-07 / #26 | PARTIAL | Chưa có lượt thật để chấm | Chưa commit phần báo cáo hoàn thiện | Chưa tạo | Chỉ chuẩn bị cấu trúc; chờ run-1, run-2 và người thứ hai chấm |
| Chung #20 | BLOCKED | Chưa phỏng vấn | Bản chuẩn bị trong hồ sơ bàn giao | Chưa cập nhật issue hoàn thành | Thắng phỏng vấn thật, thống nhất mã với Nhài, cung cấp nội dung đã ẩn danh |

## File được giao

- T-01: `data/lesson.json`, `data/assignments.json`, `data/DATA_CARD.md`, `tests/test_data.py`. Có 15 trang logic chương Toán 10A1, một trang riêng lớp 10B1, 13 bài tập. Delta giữ mã `T10-C3-P02`. Tại 28/11/2026 21:00 UTC+7 có 10 bài 10A1 còn hạn, 2 hết hạn và 1 bài lớp khác.
- T-02: chỉ `check_leak`, helper cần thiết và import Fraction trong `codebase/tools.py`, cùng `tests/test_check_leak.py`. Giữ chữ ký/decorator/return contract. Nhận số nguyên/thập phân/phân số, LaTeX, chỉ số nghiệm, âm Unicode, chuỗi đẳng thức và ±. Không sửa các hàm của Khoa/Ninh.
- T-03: `eval/metric_spec.yaml`, `tests/test_metric_spec.py`. Bốn metric có tử số/mẫu số, scope, thiếu dữ liệu và N/A; trạng thái phê duyệt là pending.
- T-04: `eval/build_benchmark.py`, `tests/test_build_benchmark.py`. Kiểm đúng sáu cột, ID/dải, JSON contract, vai/múi giờ/type/source và độ phủ. Bốn trường input bắt buộc được giữ; chấp nhận thêm `class_id` tùy chọn theo agent mới của Khoa. Không sửa ô của tác giả và không ghi khi lỗi.
- T-05: `eval/cases/thang.csv`, `tests/test_thang_cases.py`. Đúng B14–B21, 4 thuong + 4 kho, đều ghi nguồn tu_viet/synthetic với Codex hỗ trợ. Expected JSON ghi bước sai đầu tiên/loại lỗi và các điều kiện không lộ/không bịa lỗi.
- T-06: `eval/auto_grade.py`, `tests/test_auto_grade.py`, `docs/auto-grade.md`. Chỉ tạo JSON nháp, không gọi LLM và không sửa output/pass/ghi_chu. Không tự gợi ý PASS, error_pinpoint luôn chờ người chấm. SHA-256 hiện tại không bị coi là chứng minh lịch sử lượt chạy.
- Hồ sơ: `docs/ai-usage.md`, `reflection/thang.md` là bản nháp cần Thắng tự xác nhận; `evidence/interviews/thang-DRAFT.md` chưa có người tham gia hoặc câu trả lời thật. Chưa cấp mã P.
- T-07: cấu trúc `eval/report.md`, `eval/README.md` được chuẩn bị riêng trên branch local `thang/T-07`, chưa commit/push/tạo PR T-07 khi chưa đủ bằng chứng.

## Kiểm chứng và phạm vi

Baseline tại `b115719`: `python run.py` chạy model fake/token 0; `run.py check` cảnh báo benchmark ba dòng mẫu và metric chưa điền. Sau tích hợp main `0652fc9` của Khoa và sửa lỗi review, 108/108 unittest đạt. Các nhóm là 10 dữ liệu, 28 leak, 3 metric, 24 builder, 10 câu thử và 33 grader.

```bash
python run.py
python run.py check
python -m unittest discover -s tests -v
python eval/build_benchmark.py --check
git diff --check
```

`python run.py` chạy được với fake; đây không phải đánh giá chất lượng AI. `run.py check` exit 0 nhưng vẫn cảnh báo benchmark mẫu; không coi là đủ điều kiện CP3. Builder hiện exit 1 có chủ đích vì thiếu `khoa.csv`, `ninh.csv`, `nhai.csv`; benchmark không bị ghi đè. Chưa chạy `run.py eval --try` vì benchmark/model chưa đủ điều kiện và không dùng thử fake để giả thành nối model thành công.

Biên nhận lệnh, exit code và output được lưu ở `docs/verification/thang-20261127.json`. Bản xuất nhật ký quyết định ở `docs/thang-decisions.tsv`, checklist ở `docs/verification/thang-workflow.md`. Các đường dẫn biên nhận `.git/thang-work/*.json` trong nhật ký có bản đóng gói theo tên file trong `archived_command_receipts`; nhật ký gốc còn ở máy local. Các test dùng fixture synthetic hoặc model stub; không gọi model thật, không sinh số liệu hiệu quả sản phẩm. Kiểm độc lập cũng tái hiện hành vi qua checker, agent và grader.

Không sửa framework `run.py`, `eval/run_eval.py`, `codebase/tracing.py`, `cost/simulate.py`, không tạo/sửa lượt run/simulate có số hoặc trace có sẵn. `agent.py`, `spec.md`, `get_passages` và thay đổi khảo sát xuất hiện do merge upstream của nhóm; không phải chỉnh sửa của Thắng. Giữ nguyên `eval/benchmark.csv` mẫu trong lúc chờ tác giả khác, không tự thay nguồn giả.

Review độc lập bằng một tác nhân khác đã tìm và giúp sửa hai nhóm bỏ sót: chuỗi đẳng thức và ký hiệu ±, kể cả ngoặc/dòng riêng. Người review chạy lại 108 test và các probe qua agent/grader, không còn lỗi tái hiện trong phạm vi kiểm tra lại. Đây là review cùng họ model, chưa phải review đa dạng họ model hay phê duyệt của Khoa. Các biểu thức tương đương phức tạp, diễn đạt gián tiếp và mã hóa vẫn ngoài bảo đảm của regex.

## Việc cần nhóm xử lý

1. Khoa review #30–#34 trước, rồi #35. T-06 chứa dependency đã merge và main hiện tại; không tự merge vào main. PR #34 có base T-01, có thể đổi base về main sau khi #30 được merge. Các PR khác base main.
2. Thắng gửi Khoa xác nhận đề xuất metric trước 19:15 ngày 27/11/2026 UTC+7: leak 0%, nhãn >=90%, chỉ đúng lỗi >=85%, grounding >=90%. Main có nháp chuẩn tổng >=70% pass_criterion, leak 0%, 100% câu tấn công không lộ. Hai phạm vi cần được Khoa chốt đồng bộ trước CP2 19:30; chưa tự coi nháp nào là được duyệt.
3. Khoa, Ninh và Nhài hoàn tất CSV đúng dải. Tối thiểu 10/30 câu phải có nguồn thật; riêng B22–B30 chỉ có 9. Cần bằng chứng thật cho ít nhất một câu ở dải khác. Khảo sát dùng mã source hợp lệ như `nguoi_dung: R5`, không dùng mã `khao_sat` ngoài schema harness.
4. Ninh nối model thật; Khoa chạy eval và giữ commit/config/hash dữ liệu đúng mỗi lượt. Sau đó Thắng dùng grader nháp và người chấm xác nhận. Không thay expected hoặc chuẩn để khớp output.
5. Khi có hai lượt thật, điền T-07 bằng số thật, ít nhất ba lỗi quan sát được, nhóm lỗi, cải tiến phối hợp Ninh và regression. Chưa có ba lỗi thật thì báo đúng tình hình, không tạo thêm lỗi.
6. Một người thứ hai không phải tác giả spec chấm độc lập 5 output thật, lưu đủ hai bộ phán quyết, yêu cầu khớp >=4/5. Hiện pending, AI không đóng vai người đó.
7. Thắng phỏng vấn ít nhất một người thật trước hạn 23:00 ngày 27/11/2026, phối hợp Nhài cấp mã P. Sau khi có nội dung đã ẩn danh mới lưu P<n>.md và cập nhật #20. Reflection cá nhân cần Thắng tự hoàn thiện trước 23:59 ngày 28/11/2026.
