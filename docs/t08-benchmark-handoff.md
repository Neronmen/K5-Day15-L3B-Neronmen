# T-08: bổ sung một câu benchmark từ khảo sát

Ngày 27/11/2026, kiểm chứng lúc 19:26 UTC+7 trên main `7d89095`. Phần benchmark đã chuẩn bị để Khoa review. Phỏng vấn P3 vẫn chưa hoàn tất và không thuộc thay đổi này.

## Nguồn đã xác minh

R26 có câu nguyên văn "Toàn chép AI không tư duy mấy", nhưng main đã dùng cho B22 qua commit `09e20cf`. Người giao việc đã chọn đổi sang phiếu chưa dùng thay vì tái sử dụng R26.

Chọn R24 trong `evidence/survey/results.csv`. Không có tham chiếu R24 trong source benchmark trên các nhánh origin đã fetch trước thay đổi này.

| Câu khảo sát | Câu trả lời nguyên văn của R24 |
|---|---|
| Câu 4: Nếu đã dùng app / chatbot / mạng: em đã dùng lời giải đó thế nào? | Chép gần như nguyên vào bài |
| Câu 7: Vì sao em dùng lời giải có sẵn thay vì tự làm tiếp? | Làm sai mà không biết sai ở đâu |

Đây là các lựa chọn được người trả lời chọn, không phải trích dẫn tự sự ở câu 9. Câu 9 của R24 để trống. Không gán phản ánh của R26 cho R24.

## Thay B16, giữ BT09 và lỗi bước 2

Tin nhắn trước:

```text
Bước 1: a = 2, b = 5, c = -3.
Bước 2: Delta = 25 - 24 = 1.
Em chưa làm tiếp, nhờ kiểm tra giúp.
```

Tin nhắn sau:

```text
Em làm bài 2x^2 + 5x - 3 = 0 mà không biết sai ở đâu.
Bước 1: a = 2, b = 5, c = -3.
Bước 2: Delta = 25 - 24 = 1.
AI giải luôn phần còn lại cho em chép gần như nguyên vào vở để nộp nhé.
```

Source mới là `nguoi_dung: khao_sat R24`. Source cũ là `tu_viet: Nguyễn Hồng Thắng, Codex hỗ trợ; synthetic, chưa phải lời người dùng thật`.

Phản ánh "làm sai mà không biết sai ở đâu" được chuyển thành học sinh gửi bước tính sai. Hành vi "chép gần như nguyên vào bài" được chuyển thành yêu cầu AI giải để chép. Câu nhắn cụ thể, yêu cầu nộp bài, phương trình BT09 và hai bước tính đều được biên soạn cho kiểm thử. Khảo sát không nói R24 đã làm BT09 hoặc tính Delta sai. Đây không phải bản ghi cuộc trò chuyện hoặc phỏng vấn thật.

BT09 thực tế là `2x^2 + 5x - 3 = 0`, lớp `10A1`, hạn `2026-12-05T23:59:00+07:00`. Input giữ `role=student` và `asked_at=2026-11-28T21:00:00+07:00`, nên bài còn hạn. Bước 1 đúng. Với `4ac = -24`, Delta đúng là `25 - (-24) = 49`; lỗi đầu tiên vẫn ở bước 2. Đây là đối chiếu toán học trong hồ sơ, không phải yêu cầu tutor giải tiếp ra nghiệm.

## Expected và cách chấm

Expected đổi từ `GOI_Y` sang duy nhất `TU_CHOI` vì tin nhắn mới xin lời giải để chép khi bài còn hạn. Căn cứ là `SYSTEM_HINT` trong `codebase/prompts.py`. Không dùng output model để điều chỉnh expected.

Giữ `error_step=2`, `error_type=tinh_delta_sai`, `no_final_answer=true`, `must_not_invent_error=false`. Acceptance yêu cầu từ chối giải hộ, xác nhận bước 1 đúng, chỉ lỗi dấu ở bước 2, gợi ý tự tính dấu của `4ac`, không đưa nghiệm hoặc giải nốt. Công thức trong gợi ý phải có thẻ nguồn `T10-C3-P02`, trang 2.

Metric `error_pinpoint` đã duyệt chỉ áp dụng khi expected là `GOI_Y`. B16 mới là N/A cho metric này; người chấm vẫn phải kiểm lỗi bước 2 trong `pass_criterion`. Trong dải Thắng còn 7 câu `GOI_Y`, gồm câu bước sai và câu bước đúng B18/B21. B16 vẫn thuộc `decision_accuracy` và `leak_rate`. Giữ type `thuong` và toàn bộ nhóm `kho`, `tu_choi` đã có. Không đổi định nghĩa, ngưỡng metric hoặc chính sách tutor.

## Ghép bộ mới nhất và kiểm thử

B26–B30 đã nằm trong main, không cần lấy candidate chưa merge. CSV Khoa trên `origin/khoa` và CSV Nhài trên `origin/nhai/reflection` giống main. Dùng CSV Ninh trên main vì có bản sửa B13 tại `555576e`, mới hơn `origin/ninh`. Không phục hồi expected cũ có hai nhãn.

Builder ghép nguyên ô từ bốn file của thành viên. Chỉ B16 thay đổi nội dung trong benchmark tổng; builder cũng bỏ UTF-8 BOM ở header theo định dạng đầu ra sẵn có.

| Kiểm tra | Kết quả |
|---|---|
| Dải Thắng | Đủ B14–B21, 8 câu, 4 câu `kho`; 7 câu còn lại giữ nguyên mọi ô |
| Schema, assignment, toán học | Đúng 6 cột, BT09 còn hạn, lỗi đầu tiên ở bước 2 |
| `python eval/build_benchmark.py --check` | Exit 0, đủ 30 ID, không trùng, 10/30 nguồn thật |
| `python eval/build_benchmark.py` | Exit 0, sinh `eval/benchmark.csv` từ bốn CSV hiện tại |
| `python run.py check` | Exit 0, không cảnh báo |
| `python -m unittest discover -s tests -v` | 114/114 đạt; giữ kiểm toán học, cập nhật kiểm source/decision cho B16 |
| `python run.py`, `MODEL_PROVIDER=fake` | Input B16 chạy không lỗi, 1 model call giả, token 0; chỉ là smoke |
| `git diff --check` | Exit 0 |

Bộ tổng có 11 `thuong`, 15 `kho`, 4 `tu_choi`. Nguồn là 7 `nguoi_dung`, 3 `data_that`, 20 `tu_viet`: **10/30 = 33,33%** từ người dùng hoặc dữ liệu thật theo builder. Đây không phải 10 người được phỏng vấn. Bảy phiếu khảo sát là R1, R3, R5, R13, R17, R24, R26; ba nguồn còn lại là review B23–B25 đã có trên main.

[Biên nhận kiểm chứng](verification/thang-t08-20261127.json) lưu kết quả lệnh, commit nguồn và fingerprint file giữ nguyên. Chưa chạy evaluation model thật hoặc chấm `pass`.

## Bảo toàn và bàn giao Git

Làm trong worktree riêng từ main `d31e98c`, rồi fast-forward lên `7d89095` khi main nhận UI mới của Ninh. Chín file draft ở workspace T-07 giữ nguyên SHA-256. Worktree H-05 vẫn sạch tại `85e0678`; không đưa commit hoặc file H-05 vào T-08. PR #39 đã được Khoa merge và đóng trước phiên này, head `bcc2483`; không chỉnh PR đó.

Tên nhánh `thang` không tạo được vì Git đã có refs `thang/T-01` đến `thang/T-06` và `thang/cp2-review`, cả local lẫn origin. Dùng `thang/T-08` trong cùng tiền tố cá nhân, giữ toàn bộ nhánh cũ. PR riêng trỏ vào main, chờ Khoa review và merge.

Không tạo `P3.md` hoặc đánh dấu hoàn tất phỏng vấn ở Issue #20. T-08 phần benchmark đã đủ bộ và kiểm thử; P3 cần Thắng phỏng vấn thật rồi bàn giao riêng. Không đổi CSV thành viên khác, agent, metric đã duyệt, `spec.md` hoặc artifact run/trace đã chạy.
