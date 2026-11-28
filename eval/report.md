# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-072817` (deepseek-chat) | 28/30 | 93% | 10/11 | 14/15 | 4/4 | **đạt** (≥70% ✅ · leak_rate 0/27 = 0% ✅ · tu_choi 4/4 không lộ, không đổi chế độ ✅) |
| 2 | | __/__ | | __/__ | __/__ | __/__ | đạt / chưa |

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

- Nhắm vào nhóm lỗi: __ — vì sao là nhóm **đau nhất với người dùng**: __
- Đã sửa gì (có thể vài thay đổi cùng nhắm nhóm lỗi đó): __
- Kết quả: nhóm lỗi đó __/__ → __/__ · tổng __% → __%
- Câu nào **tệ đi** sau khi sửa: __

## 4. Còn lại

- Lỗi chưa sửa + nguy hiểm thế nào: __
- Nếu có thêm 1 tuần: __
