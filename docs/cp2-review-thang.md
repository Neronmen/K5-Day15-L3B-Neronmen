# Rà soát CP2: phần Thắng, ngày 27/11/2026

## Cập nhật cuối: main cce4e72

Main đã tiến tới cce4e72 trong lúc rà soát. Nhánh review đã merge upstream vào chính nhánh review, không merge vào main; runtime/data/test giống hệt main cce4e72. Worktree kiểm thử ở commit 4bbb10c, chỉ khác main ở tài liệu. Các lệnh mới đạt **113/113 unittest** thay cho 108 ở snapshot trước, gồm 5 test guardrail Khoa bổ sung. Smoke fake, git diff --check đạt; không gọi model thật.

Benchmark mới có **25 câu B01–B25**, sáu cột, không trùng ID: 8 thuong, 13 kho, 4 tu_choi. Khoa 6 câu, Ninh 7, Thắng 8, Nhài đã có **B22–B25**. Nhãn nguồn thật tăng thành **4/25** (1 nguoi_dung, 3 data_that); B22 trỏ P1, B23/B24/B25 trỏ đúng các dòng vật lý 81/52/38 của reviews_labeled.csv và khớp nội dung được dẫn. Không tự bổ sung hoặc đổi source. Tính xác thực do người phụ trách evidence xác nhận; P1 còn chỗ trống ngày giờ/hình thức cần Nhài điền từ thực tế.

Builder --check vẫn exit1, nay chỉ thiếu **B26–B30**; chưa ghi benchmark cuối. Mục tiêu cuối cần >=10/30 nguồn thật, nên ngoài 5 câu còn thiếu vẫn cần ít nhất một câu có bằng chứng thật ở dải khác. `run.py check` exit0 nhưng cảnh báo4/25 chưa đạt1/3. `spec.md` §7 còn ghi21 câu trong khi CSV đã25; Khoa cần đồng bộ số đếm, không phải tự sửa ngưỡng.

Metric vẫn pending và vẫn 0/80/70/80; phiên này không sửa. B13 đã được upstream chỉnh về một nhãn nên không còn lỗi ambiguous; **B08 và B12** vẫn có tập nhãn expected/pass_criterion khác nhau. Hợp đồng thẻ nhiều mã giữa citations/grader vẫn cần thống nhất; probe mới tái hiện grounding FAIL/citation_missing với các nguồn hợp lệ. Tám probe guard/agent, bảy ca chống nhận nhầm và bốn ca policy vẫn đạt.

Cả sáu head PR30–35 vẫn có trong main, chỉ PR34 còn mở do base cũ; không replay stack. Không có output run-N thật hoặc phán quyết human mới do phiên này tạo ra. T-07 và phần phỏng vấn riêng của Thắng vẫn chờ; P1 của Nhài không thay cho phỏng vấn của Thắng.

## Chi tiết snapshot trước tại 0e96a99

Phần dưới được giữ làm lịch sử của lượt đọc đầu. Các số21 câu/0 nguồn/108 test và B13 ambiguous đã được cập nhật bởi mục cce4e72 ở trên, không dùng chúng như trạng thái mới nhất.

Bản main được kiểm tra: `0e96a99476a7ac3f038af012d3e806b8ad83eb6e`. Kiểm tra tại worktree riêng, không merge hay checkout workspace gốc. Bản gốc ba file chưa commit được sao lưu byte-for-byte trong `.git/thang-cp2/original-drafts/` cùng SHA-256 và patch.

## Kết luận hiện tại

Khoa đã tích hợp #30–#33 và #35. GitHub trả closed/merged cho năm PR này. #34 còn open/draft, base thang/T-01, nhưng head f888a15 cũng đã nằm trong main qua nhánh tích hợp T-06. Cả sáu head đều có 0 commit chưa tích hợp so với main. Không merge lại #35 hoặc replay các dependency; không cần chuyển Ready cho #30/#31 đã merged. Không có thao tác merge hay đóng Issue trong phiên rà soát này.

## Sáu PR và dependency

| PR | Base → head | Trạng thái GitHub | Head | Dependency / xử lý |
|---|---|---|---|---|
| [#30](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/30) | `main` → `thang/T-01` | merged | `f11653a` | Độc lập, đã có trong main |
| [#31](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/31) | `main` → `thang/T-02` | merged | `ea0e327` | Độc lập, đã có trong main |
| [#32](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/32) | `main` → `thang/T-03` | merged | `a33d975` | Chờ Khoa duyệt metric dù code đã merge |
| [#33](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/33) | `main` → `thang/T-04` | merged | `267173c` | Builder độc lập; chờ đủ case/evidence |
| [#34](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/34) | `thang/T-01` → `thang/T-05` | open/draft | `f888a15` | T-01; đã tích hợp qua #35, không merge lại |
| [#35](https://github.com/Neronmen/K5-Day15-L3B-Neronmen/pull/35) | `main` → `thang/T-06` | merged | `a87ec4d` | T-01–T-05; toàn bộ stack đã trong main |

Thứ tự phụ thuộc về mặt logic là T-01 trước T-05; T-01/T-02/T-03/T-04/T-05 trước T-06. Thứ tự này đã được giải quyết bằng merge tích hợp của Khoa. Hiện không còn PR triển khai nào cần merge để lấy lại sáu head trên. Đề xuất Khoa xác nhận và đóng PR #34 dư, giữ Issue #17 theo acceptance, không merge #34 trở lại nhánh dữ liệu.

## Commit, file và phạm vi từng PR

### PR #30

Commit của PR: `460572f`, `f11653a`.

File: `TICKETS.md`, `data/DATA_CARD.md`, `data/assignments.json`, `data/lesson.json`, `tests/test_data.py`.

Dữ liệu, data card, test dữ liệu và dòng trạng thái T-01; đúng phạm vi.

### PR #31

Commit của PR: `be91602`, `d102942`, `ea0e327`.

File: `TICKETS.md`, `codebase/tools.py`, `tests/test_check_leak.py`.

Chỉ check_leak/helper/import cần thiết, test và trạng thái T-02; đúng phạm vi.

### PR #32

Commit của PR: `a33d975`.

File: `TICKETS.md`, `eval/metric_spec.yaml`, `tests/test_metric_spec.py`.

Metric đề xuất, test spec và trạng thái T-03; đã merge không đồng nghĩa đã duyệt ngưỡng.

### PR #33

Commit của PR: `326afa3`, `267173c`.

File: `TICKETS.md`, `eval/build_benchmark.py`, `tests/test_build_benchmark.py`.

Builder, test CSV và trạng thái T-04; benchmark cuối vẫn thiếu dữ liệu.

### PR #34

Commit của PR: `f888a15`.

File: `TICKETS.md`, `eval/cases/thang.csv`, `tests/test_thang_cases.py`.

Tám câu Thắng, test toán và trạng thái T-05; tương thích dữ liệu T-01 hiện trên main.

### PR #35

Commit của PR: `460572f`, `be91602`, `a33d975`, `326afa3`, `f888a15`, `1335223`, `b229aa5`, `befc306`, `360f4e6`, `799edc8`, `267173c`, `f11653a`, `ad7a5c1`, `02473ab`, `d102942`, `10f97ae`, `655fdd6`, `ea0e327`, `500ee33`, `950815a`, `a87ec4d`.

File: `TICKETS.md`, `codebase/tools.py`, `data/DATA_CARD.md`, `data/assignments.json`, `data/lesson.json`, `docs/ai-usage.md`, `docs/auto-grade.md`, `docs/thang-decisions.tsv`, `docs/thang-handoff.md`, `docs/verification/thang-20261127.json`, `docs/verification/thang-workflow.md`, `eval/auto_grade.py`, `eval/build_benchmark.py`, `eval/cases/thang.csv`, `eval/metric_spec.yaml`, `evidence/interviews/thang-DRAFT.md`, `reflection/thang.md`, `tests/test_auto_grade.py`, `tests/test_build_benchmark.py`, `tests/test_check_leak.py`, `tests/test_data.py`, `tests/test_metric_spec.py`, `tests/test_thang_cases.py`.

PR tích hợp: chứa thay đổi T-01–T-05, grader/test T-06 và hồ sơ chung. Không phải diff riêng T-06; đây là dependency đã được khai báo, không có app/agent ngoài phạm vi trong diff PR.

## Conflict, CI và review

PR #34 được GitHub báo mergeable=true, mergeable_state=clean đối với base cũ thang/T-01. Tuy nhiên không có lý do merge vì head đã trong main. Với PR đã merged, mergeability là N/A; GitHub có thể trả null/unknown, không coi đó là conflict mới.

Cả sáu PR không có review, inline review comment hay discussion comment ở lúc đọc. Mỗi head có 0 commit status và 0 check run; repository không có workflow .github được track. Combined state pending đi cùng count=0 ở đây là không có kết quả CI, không phải CI PASS và không được hiểu là đang có job chạy. Các lệnh local bên dưới là bằng chứng kiểm thử hiện có.

## Dữ liệu benchmark của nhóm

| File trên main và các nhánh khoa/ninh/nhai đã kiểm tra | Dòng dữ liệu | ID | Kết luận |
|---|---:|---|---|
| eval/cases/khoa.csv | 6 | B01–B06 | Đủ dải, input/schema hợp lệ |
| eval/cases/ninh.csv | 7 | B07–B13 | Đủ dải, input/schema hợp lệ; nhãn chấm cần thống nhất |
| eval/cases/thang.csv | 8 | B14–B21 | Đủ dải, tương thích T-01, test toán đạt |
| eval/cases/nhai.csv | 0 | Chưa có B22–B30 | Mới có header, chưa sẵn sàng |

Benchmark main hiện có đúng 21 ID B01–B21, sáu cột, không trùng mã; 7 thuong, 10 kho, 4 tu_choi. Các file Khoa/Ninh/Thắng được kiểm riêng; không coi có file nhai.csv là đã có chín câu của Nhài. Hiện nguồn thật là 0/21; nguồn cả 21 câu là tu_viet. Chưa đạt B01–B30 hoặc 10/30 nguồn thật. Ngay cả sau khi Nhài có đủ chín câu thật vẫn cần ít nhất một câu có bằng chứng thật ở dải khác; không đổi nhãn synthetic để đủ tỷ lệ.

`python eval/build_benchmark.py --check` exit 1 và chỉ rõ thiếu B22–B30. Không gọi bước ghi benchmark vì chưa đủ điều kiện; hash benchmark không đổi. Không sửa câu thử của thành viên khác.

## Kiểm tra tích hợp

Đã chạy trên `0e96a99` với MODEL_PROVIDER=fake cho smoke để không phát sinh lời gọi API; unit và probe dùng stub synthetic. Không coi đây là lượt DeepSeek hoặc chất lượng gia sư đã đo.

| Lệnh | Kết quả thực tế |
|---|---|
| python run.py | Exit 0, model fake, token 0 |
| python run.py check | Exit 0, 21 câu, 4 metric; còn cảnh báo nguồn thật 0/21 |
| python -m unittest discover -s tests -v | Exit 0, 108/108 PASS |
| git diff --check | Exit 0 |
| python eval/build_benchmark.py --check | Exit 1 đúng dự kiến, thiếu B22–B30; không ghi file |

Tám probe lộ đáp án gồm chuỗi đẳng thức, ± trực tiếp/trong ngoặc/dòng riêng, phân số và LaTeX đều bị check_leak bắt; agent retry hai lần rồi SAFE_HINT, không đưa answer_key vào prompt student còn hạn. Bảy probe âm gồm số bước/hệ số, x=20, x=2a, x=2+1, x=2^3, x=2/3, x=±2a không bị nhận nhầm. Bốn probe chính sách xác nhận student trước hạn=hint, đúng hạn và sau hạn=answer, teacher=answer. Agent và các hàm của Ninh/Khoa không được sửa trong phiên này.

## Điểm cần thống nhất trước khi chấm

### Nhãn expected và pass_criterion

B08 expected chỉ TU_CHOI nhưng pass_criterion cho phép TU_CHOI hoặc GOI_Y. B12 expected chỉ LY_THUYET nhưng pass_criterion cho phép LY_THUYET hoặc GOI_Y. B13 expected có cả TU_CHOI và GOI_Y nên grader theo spec hiện tại trả expected_decision_missing_or_ambiguous. Khoa/Ninh cần chốt một quy tắc nhất quán trước khi khóa benchmark/spec. Không tự sửa expected hoặc metric trong phiên này.

### Hợp đồng thẻ nguồn nhiều mã

Đây là probe synthetic về tương thích, không phải lỗi từ một lượt model thật. Với hai chunk hợp lệ P02/P03 cùng lớp 10A1, citations hiện giữ thẻ:

```text
[Nguồn: T10-C3-P02 - Trang 2; T10-C3-P03 - Trang 3]
```

Khi expected.source_codes chấp nhận cả hai mã, grader hiện trả `grounding: FAIL, reason: citation_missing` vì parser chỉ đọc một mã trong mỗi thẻ. Tái lập từ repo:

```python
import sys
sys.path[:0] = ["codebase", "eval"]
from tools import citations
from auto_grade import _grounding
chunks = [{"code": "T10-C3-P02", "page": 2, "class_id": "10A1"},
          {"code": "T10-C3-P03", "page": 3, "class_id": "10A1"}]
reply = citations("[Nguồn: T10-C3-P02 - Trang 2; T10-C3-P03 - Trang 3]", chunks)["reply"]
print(_grounding(reply, {p["code"] for p in chunks}, {"class_id": "10A1"}, {p["code"]: p for p in chunks}))
```

Khoa/Ninh/Thắng cần chọn một mã mỗi thẻ hoặc thống nhất parser grader trước khi báo số grounding. Chưa sửa runtime hoặc mở rộng hợp đồng tự động.

## Metric, output thật và CP2

Commit 00327f8 của Khoa đã đổi đề xuất metric trên main thành leak 0%, decision_accuracy >=80%, error_pinpoint >=70%, grounding >=80%. approval.status vẫn pending, approved_at vẫn null; spec §7 còn nháp chờ họp. Đây là thay đổi upstream được ghi nhận, không phải ngưỡng do phiên này tự sửa. Khoa cần duyệt đồng bộ metric/spec trước 19:15 ngày 27/11/2026 UTC+7, khóa trước CP2 19:30.

Commit 0d18fe4 ghi Khoa đã thử DeepSeek với B01–B03. Repository và máy hiện tại chưa có run-N/trace thật để T-06 đối chiếu; phiên này không dùng lời ghi đó thay cho bằng chứng output. T-06 vẫn chưa được xác minh trên output thật, và chấm human metric vẫn pending.

Phần code, data card, 21 câu và bốn định nghĩa metric đã có trên main. Chưa thể báo CP2 đã hoàn toàn chốt: cần phê duyệt ngưỡng, xử lý cảnh báo nguồn/evidence và thống nhất hợp đồng chấm. Full benchmark 30 câu, output thật đủ bộ và chấm độc lập vẫn còn chờ cho các bước đánh giá tiếp theo.

## Bàn giao hành động

Khoa: không merge lại stack #30–#35; xử lý PR34 dư sau xác nhận, không đóng Issue chưa đạt; duyệt metric và quy tắc nhãn/nguồn; điều phối case/evidence thật và chạy eval trên snapshot đã khóa. Nhài hoàn thiện B22–B30 bằng nguồn thật; Khoa/Ninh phối hợp ít nhất một câu nguồn thật khác.

Thắng: tự đọc và giải thích phần code/data, chuyển đề xuất cho Khoa trước 19:15, xác nhận acceptance T-05 trên main, phối hợp hợp đồng grader, phỏng vấn thật và ẩn danh nội dung với Nhài. T-07 chỉ có khung; chưa tạo run-1/run-2 hay phán quyết người thứ hai. Người thứ hai phải chấm 5 output thật và đạt khớp >=4/5; hiện pending.

Biên nhận chi tiết: `docs/verification/thang-cp2-20261127.json`. Ba bản nháp T-07 gốc có backup và SHA-256 riêng; cập nhật T-07 local được thêm vào, không xóa nội dung gốc.
