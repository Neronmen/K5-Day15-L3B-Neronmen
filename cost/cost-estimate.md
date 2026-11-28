# Chi phí MinutesStudy Tutor, đã chạy 50 phiên model thật

Cập nhật 27/11/2026 sau main `4d1f81c`. Đã kế thừa và kiểm lại phân tích khảo sát, ba persona, ba quy mô và giá chính thức. Người giao việc cấu hình OpenAI/gpt-6-luna local; đã chạy 10 phiên thử và 50 phiên chính thức bằng API thật. Token từ usage đã đối chiếu trace. Chi phí/task thành công vẫn pending vì chưa có tỷ lệ đạt do người chấm xác nhận; không lấy lỗi kỹ thuật bằng 0 làm chất lượng đạt.

## Khảo sát và persona

Nguồn là `evidence/survey/results.csv`, bản ẩn danh 26 phiếu của Nhài đã nằm trong main. Git blob hiện tại khớp snapshot `08e05ba26b980c5a17c8a909580c4d477ff7b473`, SHA256 `05ba7a50928d9252555e6506a95a210190a706264d7471d29bdca104473c9939`. [Bản tổng hợp gốc](survey-q5-analysis.json) giữ thời điểm phân tích cũ. Phiên này chạy lại script trên origin/main và đối chiếu mọi số tổng hợp, không thay survey.

Tổng 26 học sinh lớp 10–12, Q5 hợp lệ 26, thiếu 0, không hợp lệ 0, loại ngoài THPT 0. Đây là snapshot thuận tiện, chưa phải khảo sát đã đóng hoặc mẫu đại diện cho cả trường.

| Q5, lần dùng app/chatbot mỗi tuần | Số người | Tỷ lệ trên 26 |
|---|---:|---:|
| 0 | 3 | 11,54% |
| 1–2 | 4 | 15,38% |
| 3–5 | 2 | 7,69% |
| 6–10 | 7 | 26,92% |
| Trên 10 | 10 | 38,46% |

Giữ cả ba người chọn 0 trong mẫu số và trung bình nhóm. Q5 chưa đo adoption MinutesStudy hoặc số câu hỏi trong mỗi phiên.

| Persona | Nhóm Q5 | Số người | Share | Phiên/người/tháng theo giả định |
|---|---|---:|---:|---:|
| dung_it | 0 và 1–2 | 7 | 7/26 | 3,714286 |
| dung_vua | 3–5 | 2 | 2/26 | 17,333333 |
| dung_nhieu | 6–10 và trên 10 | 17 | 17/26 | 44,862745 |

Các giả định trong personas.yaml:

1. Khoảng đóng lấy điểm giữa 0, 1,5, 4, 8 lần/tuần. Khoảng trên 10 lấy 12, **tự ước tính**. Trung bình từng nhóm cân theo số người trong các khoảng.
2. Một tháng bằng 52/12 tuần. Công thức là trung bình lần/tuần × 52/12. Không so trực tiếp với impact dùng tháng bốn tuần trong spec khi chưa đồng nhất đơn vị.
3. Một lần dùng là một phiên, mỗi phiên một câu hỏi độc lập, **tự ước tính**. Khung không mang lịch sử hội thoại giữa các lượt; tăng turns không tự biến thành đối thoại nhiều lượt.
4. Cohort thay app cũ bằng MinutesStudy với cùng tần suất, adoption 100%, **tự ước tính**. Adoption 25% hoặc 50% làm phần khối lượng kỳ vọng giảm tương ứng nếu các giả định khác giữ nguyên.

Trung bình toàn mẫu là 31,666667 phiên/người/tháng theo mô hình, không phải log sử dụng thật. Người chọn 0 vẫn nằm trong trung bình dung_it; không gán số lần dùng dương cho từng người đó.

## Ba quy mô và độ nhạy

Low/base/high tương ứng 300/1000/3000 học sinh, đều **tự ước tính**. Cơ sở 1000 theo giả định một trường trong spec; 300 đại diện một khối, 3000 đại diện ba trường. Không có cam kết triển khai hoặc nguồn chứng minh quy mô thực tế.

| Giả định nhóm trên 10, lần/tuần | Phiên/người/tháng | Low 300 | Base 1000 | High 3000 |
|---|---:|---:|---:|---:|
| 11, tối thiểu nguyên | 30 | 9000 | 30000 | 90000 |
| 12, baseline tự ước tính | 31,666667 | 9500 | 31666,67 | 95000 |
| 20, stress tự ước tính | 45 | 13500 | 45000 | 135000 |

Khoảng trên 10 không có cận trên hữu hạn; 20 không phải trần có bằng chứng. Giả định hai hoặc bốn câu hỏi độc lập mỗi phiên làm số lượt hỏi tăng hai hoặc bốn lần, chưa phải mức tăng tiền thực đo. Phiên hội thoại thật có thể tăng cả độ dài ngữ cảnh.

## Giá và model đo, ngày xem 27/11/2026

Đơn vị USD trên một triệu token. Dùng paid standard hoặc paid peak, mọi input tính uncached. Chưa đo tỷ lệ cache hit, chưa áp free tier, batch hoặc quy đổi VND.

| Model | Input uncached | Input cached | Output | Nguồn và giới hạn |
|---|---:|---:|---:|---|
| gpt-6-luna | 0,10 | 0,01 | 0,50 | [OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna), standard text; cache write 0,125 USD/triệu token chưa hạch toán riêng |
| deepseek-flash | 0,30 | 0,006 | 1,20 | [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/), giá peak để định giá bảo thủ |
| gemini-2.5-flash-lite | 0,10 | 0,01 | 0,40 | [Gemini](https://aistudio.google.com/docs/pricing#gemini-2.5-flash-lite), paid standard text; output gồm thinking |

DeepSeek off-peak là 0,15 input uncached và 0,60 output. Không áp giá peak tham chiếu thành hóa đơn thực tế. Gemini cache còn phí lưu 1 USD/triệu token/giờ; cấu hình này không dùng cache storage hoặc Search/Maps. OpenAI/gpt-6-luna đã gọi thành công qua Chat Completions. Đã sửa adapter ai.py gửi max_completion_tokens cho các model reasoning OpenAI và bỏ temperature; giữ usage.completion_tokens nguyên vẹn, không cộng reasoning lần nữa. Test tái hiện lỗi max_tokens trước sửa và đạt sau sửa; prompt/chính sách không đổi. Giá gpt-4.1-mini trong receipt tra cứu đầu phiên chỉ là lịch sử, không dùng để tính lượt Luna.

[Receipt tải lại nguồn giá](price-refresh-20261127.json) và [giá đúng model Luna](openai-luna-price-20261127.json) lưu URL, thời điểm và SHA256 nội dung. Receipt Luna được ghi trước lượt chạy nên usage_measurement_available=false phản ánh đúng thời điểm đó; usage thật nằm trong receipt/analysis simulate-1. [Receipt giá trước](price-sources-20261127.json) giữ làm lịch sử. Giá model Y áp lên token model X chỉ là định giá đối chiếu; hai tokenizer không được mặc định cho cùng token.

## Trạng thái lượt chạy

Benchmark đã đủ 30 câu, 10/30 nguồn thật sau PR #45; PR #46 đã đồng bộ README. P3 không còn là dependency của benchmark hoặc H-05. Nghĩa vụ phỏng vấn thật vẫn riêng, chưa hoàn tất.

Đã lưu [lock benchmark và metric](../eval/frozen-inputs-20261127.json) từ main 4d1f81c. Kiểm trước và sau evaluation bằng `python eval/verify_frozen_inputs.py`. Lock dùng SHA256 byte UTF-8 với LF, kèm hash byte checkout và Git blob để phân biệt CRLF trên Windows. Không sửa benchmark, metric hoặc chuẩn đạt.

Người giao việc đã tạo .env local với OpenAI/gpt-6-luna. Secret chỉ được truyền qua environment của process, không sao chép vào worktree, manifest, snapshot, trace hoặc Git. Không sửa .env của người dùng.

Lượt smoke B16 trên adapter cũ nhận HTTP 400 vì max_tokens. Sau sửa tương thích tham số, B16 trả TU_CHOI đúng loại yêu cầu, chỉ lỗi dấu Delta ở bước 2, usage 2268 input/495 output. Đây là smoke thật, không phải run đánh giá đã chấm. Một probe seed 42 đầu tiên chọn câu được code xử lý nên token 0; khung ghi simulate-mock, được giữ và không tính là phép đo model.

Lượt thử 10 phiên: 8 model calls, 14316 input/1589 output, không lỗi. Dự toán 50 từ trial là 0,0111305 USD uncached, dự phòng ba lần 0,0333915 USD; đây là dự toán trước chạy, không phải tiền thực thu. Trial thiếu dung_vua nên không dùng summary trial để kết luận tiền riêng cho persona đó. Lượt chính thức có đủ ba persona.

Lượt chính thức `simulate-1@20261127-211403`: 50 phiên, 45 model calls, 84621 input/10106 output, không lỗi kỹ thuật, năm phiên code-only. Persona dung_it 16 phiên, dung_vua 2, dung_nhieu 32. Nhóm dung_vua chỉ hai mẫu nên ước lượng tiền riêng nhạy với nội dung được chọn. Seed 42 tái lập kế hoạch lấy câu; output API không đảm bảo giống nguyên văn khi chạy lại.

[CSV gốc](simulate-1.csv), [trace](../traces/simulate-1.jsonl), [summary khung](simulate-1-summary.md), [manifest trước chạy](simulate-1-manifest.json), [receipt](simulate-1-receipt.json), [phân tích đối chiếu](simulate-1-analysis.json) được giữ nguyên. Snapshot byte input lúc chạy ở cost/inputs/simulate-1; code adapter tại ef61707, các file khác có SHA256 trong manifest. Manifest lưu trạng thái dirty cùng hash từng input, không giả là một checkout sạch. Hash benchmark/metric đã kiểm đúng trước và sau lượt.

Worktree H-05 cũ có lượt simulate --try bằng fake: 10 phiên, 8 model-call giả, token 0/0, exit 1 vì mock. CSV/trace cũ giữ nguyên byte tại .git/thang-h05/worktree, không tạo lại hoặc dùng làm số chi phí. [Receipt lượt mock cũ](h05-verification-20261127.json) giữ làm lịch sử; blocker 9/30 trong receipt cũ đã được giải quyết, không phải trạng thái hiện tại.

Chưa tìm thấy eval/run-N.csv hoặc trace evaluation thật của nhóm trên các nhánh origin, các worktree, GitHub Actions artifacts hoặc Releases đã kiểm tra trước lượt simulation này. Simulation mới là phép đo chi phí, không thay bộ evaluation đã chấm. Issue #21/#24/#26 cũng chưa có comment bàn giao output. Đây là phạm vi đã kiểm, không khẳng định thành viên chưa chạy ở nơi khác.

## Phần còn phụ thuộc evaluation

T-06 đã có công cụ grader, nhưng không có run-N.csv của nhóm để đối chiếu output và expected. T-07 vẫn cần hai lượt cùng benchmark/metric đã khóa, ít nhất ba lỗi có bằng chứng, human grading và người thứ hai chấm năm output. Không tự điền pass, tạo run-2 hoặc tính đạt 100%.

Chỉ tính USD/task thành công khi có tỷ lệ đạt đã chấm cùng model/phạm vi. `--rate-from` sẽ chạy simulation mới; khi có human rate, dùng dữ liệu 50 phiên đã đo để tính lại báo cáo riêng, không sửa CSV/trace/summary gốc hoặc tiêu token lần nữa chỉ để thay tỷ lệ.

Retry mạng không được adapter hạch toán từng HTTP attempt; không suy số retry bằng 0 từ 45 model-call events. Các model-call thành công có token usage, không có phiên lỗi trong lượt chính thức; chưa đối chiếu account billing. Input đều dưới 272K token nên không áp long-context uplift. Báo cáo tính toàn input uncached, chưa tách cached input hoặc cache-write surcharge; vì vậy đây là token-price reference estimate, không phải hóa đơn.

## Chi phí và impact

| Giá áp dụng trên token Luna | USD/phiên | USD/task thành công | Low/tháng | Base/tháng | High/tháng | USD/học sinh/tháng |
|---|---:|---|---:|---:|---:|---:|
| gpt-6-luna | 0.000270302 | pending human rate | 2.456322 | 8.187740 | 24.563219 | 0.008187740 |
| deepseek-flash | 0.000750270 | pending human rate | 6.832526 | 22.775087 | 68.325262 | 0.022775087 |
| gemini-2.5-flash-lite | 0.000250090 | pending human rate | 2.277509 | 7.591696 | 22.775088 | 0.007591696 |

Luna là token thực đo. Hai hàng DeepSeek/Gemini chỉ là định giá trên token Luna, không phải chi phí hoặc chất lượng thực đo của hai model đó. Toàn lượt 50 tương đương 0,0135151 USD ở giá Luna uncached; trial tương đương 0,0022261 USD; smoke B16 tương đương 0,0004743 USD theo cùng phép tính. Không gộp các số này thành hóa đơn đã xác minh.

Công thức tháng là `Σ(users × share × uses_per_month × mean_cost_of_persona_session)`. USD/học sinh/tháng là tiền tháng chia số học sinh cùng cohort. Chi phí/task thành công bằng tiền bình quân chia tỷ lệ đạt đã chấm, nếu cùng phạm vi và tỷ lệ lớn hơn 0. Không mặc định đạt 100% hoặc lấy tỷ lệ lỗi kỹ thuật làm tỷ lệ đạt sư phạm.

Khảo sát chưa chứng minh tutor giảm bao nhiêu lần chép hoặc tiết kiệm bao nhiêu giờ. Không lấy số phiên mô hình hóa làm số lần chép đã tránh. Ở quy mô tự ước tính 1000 học sinh, mức tham chiếu Luna 8,187740 USD/tháng phục vụ khoảng 31666,67 lượt hỗ trợ theo giả định tần suất, tương đương 0,008188 USD/học sinh/tháng. Khảo sát cho thấy 14/26 chép gần như nguyên và 12/14 trong nhóm này chỉ làm được một phần hoặc không làm được bài kiểm tra cùng dạng, theo evidence/summary.md. Các tỷ lệ này mô tả cơ hội hỗ trợ, không đo hiệu quả tutor. Chưa có tác động nhân quả hoặc tỷ lệ đạt đã chấm nên chưa tính lợi ích ròng/ROI, không gán mỗi phiên là một lần chép đã tránh. Hosting, lưu trữ, người duyệt và thuế/phí chưa nằm trong giá token.

## Tái lập phần đã hoàn tất

```text
python cost/analyze_q5.py --git-ref origin/main
python -m unittest discover -s tests -p test_cost_q5.py -v
python eval/verify_frozen_inputs.py
python eval/build_benchmark.py --check
python run.py check
python run.py simulate --help
```

analyze_q5.py --output chỉ ghi tên snapshot mới, không ghi đè snapshot cũ. Phép kiểm và tiến độ Issue ở [hồ sơ rà soát Thắng](../docs/thang-issue-audit-20261127.md).
