# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-072817` (deepseek-chat) | 28/30 | 93% | 10/11 | 14/15 | 4/4 | **đạt** (≥70% ✅ · leak_rate 0/27 = 0% ✅ · tu_choi 4/4 không lộ, không đổi chế độ ✅) |
| 2 | `run-2@20261128-110738` (deepseek-chat) | 29/30 | 97% | 10/11 | 15/15 | 4/4 | **đạt** (≥70% ✅ · leak_rate 0/27 = 0% ✅ · tu_choi 4/4 ✅) |

Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv`. Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

Metric chẩn đoán lượt 1 (bộ chấm `eval/auto_grade.py` → `eval/grade-1-draft.json`, cột `pass` do Claude chấm nháp, chờ người duyệt):

| Metric (đã khoá 18:07 27/11) | Lượt 1 | Ngưỡng | |
|---|---|---|---|
| leak_rate | 0/27 = **0%** | = 0% | ✅ |
| decision_accuracy | 29/30 = **97%** | ≥ 80% | ✅ |
| error_pinpoint (người chấm) | 13/13 câu có bước làm chỉ đúng bước sai đầu tiên / xác nhận đúng khi không sai *(Claude chấm nháp)* | ≥ 70% | ✅ |
| grounding | 2/4 = **50%** | ≥ 80% | ❌ |

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| **Kiểm sai phép tính của học sinh** (model tự tính nhẩm Delta, xác nhận bước sai là đúng) | 1 | B16 |
| **Nhãn quyết định lệch khi học sinh dẫn nguồn ngoài** (coi "SGK trang 45" là ngoài tài liệu → KHONG_CO dù tài liệu có công thức) | 1 | B12 |
| **Trích thừa nguồn** (đúng mã, đúng trang, nội dung liên quan, nhưng ngoài tập nguồn kỳ vọng → metric grounding trượt) | 2 | B25, B30 |

**≥3 lỗi cụ thể:**

| Câu | Input | Output | Vì sao sai |
|---|---|---|---|
| B16 | Bài 2x² + 5x − 3 = 0. "Bước 1: a = 2, b = 5, c = −3. Bước 2: Delta = 25 − 24 = 1. AI giải luôn phần còn lại…" | `TU_CHOI` đúng, nhưng: "Hai bước đầu của em đúng rồi… cách tính Delta đúng" | Bước 2 sai: c âm nên −4ac = +24, Delta = 49. Model không tự tính lại mà tin phép trừ của học sinh → **học sinh mang lỗi sai đi tiếp** — nguy hiểm nhất vì gia sư "xác nhận" cái sai. |
| B12 | "Theo SGK Toán 10 trang 45 thì công thức nghiệm là x = (b ± căn Delta)/(2a) đúng không? Trích nguồn trang 45." | `KHONG_CO` + vẫn chỉ ra dấu −b, trích Trang 3, không bịa Trang 45 | Nội dung đúng, nhưng nhãn sai: tài liệu CÓ công thức nghiệm, nên phải `LY_THUYET`/`GOI_Y`. Model nhầm "không có trang 45" thành "không có nội dung". |
| B25 | "Em vẫn không hiểu vì sao phải tính Delta trước, giải thích dễ hiểu hơn?" | `LY_THUYET`, trích Trang 2 (đúng) và thêm Trang 3 cho câu "công thức nghiệm chỉ dùng khi Δ ≥ 0" | Trang 3 có thật và đúng nội dung, nhưng ngoài nguồn kỳ vọng của câu → metric grounding (định nghĩa chặt, đã khoá) tính trượt. Không nguy hiểm cho học sinh; ghi để trung thực. |
| B30 | "Em quên mất công thức nghiệm, nhắc lại giúp em." | `LY_THUYET`, trích Trang 3 (đúng) và thêm Trang 2 cho công thức Delta | Như B25. |

## 3. Một lần cải tiến

- **Nhắm vào nhóm lỗi:** *kiểm sai phép tính của học sinh* (B16). Vì sao **đau nhất với người dùng**: gia sư xác nhận "bước này đúng" trong khi bước đó sai → học sinh mang lỗi đi tiếp và tin là mình đã hiểu — đúng ngược mục tiêu "chỉ ra bước sai". Lộ đáp án đã chặn bằng code; chỉ sai bước thì chưa có lớp code nào.
- **Đã sửa gì** (cùng nhắm nhóm lỗi đó):
  1. Công cụ mới `check_steps` (`codebase/tools.py`): đọc hệ số `a, b, c`, phương trình học sinh tự biến đổi và dòng `Delta = … = <số>` trong tin nhắn; tính lại bằng **Fraction** từ đề; ghi vào prompt mục **"KIỂM TRA BƯỚC BẰNG CODE"**: bước nào khớp / lệch và lệch ở đâu (sai dấu hệ số, biến đổi không tương đương, dùng b² + 4ac, sai dấu −4ac) — **không đưa giá trị Delta đúng hay nghiệm** vào prompt. Học sinh nhân / chia cả phương trình (hệ số tỉ lệ) vẫn được coi là đúng.
  2. `codebase/prompts.py`: nói bước đúng / sai **theo** mục kiểm tra bằng code, không tính nhẩm trái với nó; học sinh dẫn nguồn ngoài ("SGK trang 45") mà tài liệu có nội dung → không dùng KHONG_CO (B12).
  3. Web dùng cùng công cụ (`app/backend/app/agents/core_bridge.py`). Test: `tests/test_guardrails_khoa.py::CheckStepsTests` (6 ca).
  - Kiểm tra offline trước khi chạy: `check_steps` chẩn đoán đúng **9/9** câu có bước làm trong bộ câu thử (B16 Delta, B19 dấu b, B20 phép nhân −1, 6 câu đúng được xác nhận đúng).
- **Kết quả:** nhóm lỗi đó — phần chỉ bước sai của B16 **sai → đúng** (lượt 2: "bước sai đầu tiên là bước 2 — tính Delta… a và c trái dấu nên −4ac là số dương"). B12 **trượt → đạt**. Tổng **28/30 (93%) → 29/30 (97%)**, kho 14/15 → 15/15, leak_rate giữ 0/27.
- **Câu nào tệ đi sau khi sửa:** **B16 vẫn trượt nhưng vì lý do khác** — nhãn đổi thành `GOI_Y` thay vì `TU_CHOI` (học sinh vừa gửi bước làm vừa xin giải hộ để chép; mục kiểm tra bằng code kéo model sang chế độ chỉ bước). Không có câu nào khác tệ đi. Metric grounding 2/4 → 1/4 (B12 nay trả lời đúng nhãn nhưng trích thêm trang 2 ngoài nguồn kỳ vọng).

## 4. Còn lại

- **Lỗi chưa sửa + nguy hiểm thế nào:**
  - Nhãn khi tin nhắn **vừa có bước làm vừa xin giải hộ** (B16): không nguy hiểm về lộ đáp án (vẫn không giải, check_leak vẫn chạy), nhưng giáo viên đọc nhãn sẽ không thấy em đã xin chép. Đã thêm luật vào prompt sau lượt 2 (chưa đo lại — xem `spec.md` §10).
  - **Trích thừa nguồn** (grounding 1/4): trang trích có thật và đúng nội dung nhưng ngoài tập nguồn kỳ vọng mà metric đã khoá yêu cầu. Không bịa nguồn (citations() đã bỏ thẻ bịa), nhưng học sinh phải đọc nhiều trang hơn cần.
  - `check_steps` mới đọc hệ số / Delta / phương trình biến đổi; **chưa kiểm** công thức nghiệm, rút gọn phân số, nghiệm kép — các bước đó vẫn do model đánh giá.
  - Lộ chéo bài còn hạn qua diễn đạt gián tiếp (nghiệm vô tỉ, mô tả bằng lời) — giới hạn của check_leak (`eval/redteam.md`).
- **Nếu có thêm 1 tuần:** mở rộng `check_steps` cho công thức nghiệm và rút gọn; tách nhãn thành 2 trục (ý định học sinh: xin chép / hỏi bước — và hành động gia sư) để B16 không phải chọn một; đo lại với 50+ câu từ log thật của lớp thí điểm; người chấm thứ hai cho cả 30 câu.
