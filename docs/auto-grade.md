# Tạo bản nháp chấm eval

## Chạy công cụ

Chỉ dùng thư viện chuẩn Python. `eval/auto_grade.py` đọc file lượt chạy và tạo gợi ý; không gọi LLM, không sửa file nguồn, không điền cột `pass` thay người chấm.

1. Chờ benchmark hợp lệ và Khoa chạy model thật.
2. Giữ bản gốc CSV, trace, commit và bản metric/data dùng lúc chạy.
3. Tạo báo cáo với tên file chưa tồn tại:

```bash
python eval/auto_grade.py --help
python eval/auto_grade.py eval/run-1.csv --report eval/grade-1-draft.json
```

Bỏ `--report` để in JSON ra màn hình. Đọc `review_status`, `issues` và từng mục trong `metrics`. `original` giữ nguyên các giá trị ô gốc, gồm output, pass và ghi_chu. `suggested_pass` chỉ gợi ý `0` khi có lỗi trả lời tự động xác định được; để trống khi cần người xem. Không có gợi ý PASS tự động.

4. Người chấm đọc input, output, expected và pass_criterion rồi xác nhận từng metric cần chấm tay. `error_pinpoint` luôn chờ người chấm, kể cả khi đã có pass tổng.
5. Người chấm chỉ điền `pass` và `ghi_chu` trong file run theo quy định repo. Giữ phán quyết cũ, ghi rõ nếu người chấm quyết định sửa lại.
6. Sau khi chấm đủ, chạy lệnh chính thức:

```bash
python run.py score eval/run-1.csv
```

## Khai báo nhãn và nguồn kỳ vọng

Expected dạng văn bản cần đúng một nhãn `[QUYET_DINH: ...]`. Có thể dùng JSON trong ô `expected`, giống B14–B21:

```json
{"decision":"GOI_Y","error_step":3,"error_type":"quen_2a","no_final_answer":true}
```

Với câu lý thuyết, ghi mã nguồn được chấp nhận trong `expected` hoặc `pass_criterion`. JSON có thể ghi `source_codes`, ví dụ `["T10-C3-P02"]`. Đây là tập nguồn chấp nhận: cần ít nhất một thẻ, mọi thẻ phải thuộc tập này, đúng trang và cùng lớp. Không tự lấy `lesson_codes` để thay ý tác giả. Code chỉ xác minh danh tính nguồn; người chấm kiểm tra nội dung có được nguồn hỗ trợ.

## Hiểu kết quả

`SYSTEM_ERROR` là lỗi chạy, output rỗng hoặc thiếu một câu của benchmark. `MISSING_DATA` là thiếu căn cứ chấm, input contract hỏng hoặc các ô sao chép trong run không còn khớp benchmark hiện tại. `RESPONSE_ERROR` là sai nhãn, nguồn hoặc lộ đáp án. `HUMAN_REVIEW` nghĩa là chưa phát hiện lỗi bằng code và còn cần người xác nhận.

Mỗi metric báo tử số, mẫu số, số đã kiểm tra, số chưa rõ và độ phủ. Với leak_rate, tử số là số câu bị phát hiện lộ; với metric khác là số câu đúng đã xác nhận bằng code. Câu lỗi kỹ thuật vẫn ở mẫu số khi xác định được phạm vi áp dụng. Tỷ lệ để `null` nếu có phần chưa rõ; mẫu số bằng 0 là `N/A`. Chưa có phán quyết error_pinpoint thì không công bố tỷ lệ của metric đó. Thiếu câu trong run không được loại để làm đẹp điểm.

Ngưỡng lấy từ `metric_spec.yaml`; trạng thái `pending` không biến thành chuẩn được duyệt. Kể cả sau khi duyệt, kết luận bằng code chỉ tạm thời; `ready_for_final_report` luôn false vì còn bước xác nhận bằng người và provenance.

## Dùng dữ liệu của đúng lượt

Tham số `--benchmark`, `--metric-spec`, `--assignments`, `--lessons` nhận các bản snapshot tương ứng lượt chạy. Không thay nguồn hiện tại cho lượt cũ rồi coi là so sánh cùng điều kiện. SHA-256 trong báo cáo là hash file tại lúc phân tích, không chứng minh đó là file dùng khi gọi model. `analysis_code_commit` là commit của công cụ chấm, không phải commit tạo output. Giữ model/config, commit lúc chạy, hash benchmark/spec/data và trace riêng cho mỗi lượt.

Một run có mã ngoài benchmark được báo trong `unmatched_run_ids`. Không coi là đủ bộ để báo cáo chính thức trước khi giải thích các mã này. Fixture tổng hợp, `run-try`, model giả và token 0 không phải bằng chứng CP3/CP4.

## Kiểm thử

```bash
python -m unittest discover -s tests -p test_auto_grade.py -v
```

Các fixture ghi rõ synthetic, không phải output model hay nguồn người dùng thật. Bộ chặn regex có thể bỏ sót cách diễn đạt gián tiếp, nghiệm vô tỉ, biểu thức phức tạp và mã hóa; không coi không phát hiện leak là bảo đảm không thể lộ.
