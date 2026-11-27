# Bàn giao của Thắng ngày 27/11/2026

## Snapshot hiện hành

Main đã fetch và kiểm chứng: `12250ae84e7fe0bb47e048fafd4badcc6bde3946`. Worktree `.git/thang-cp2/integration` đã merge upstream vào nhánh review của Thắng và có mã chạy, data, test, benchmark, metric giống main này. Nhánh main và worktree gốc `thang/T-07` không được checkout hoặc rebase. PR #39 tiếp tục là draft để Khoa review; không merge lại #34 hoặc stack T-01 đến T-06.

Metric đã được Khoa duyệt tại `ae5bc562866a218c7b96e2da75fe204002cf16db`, lúc **18:07 ngày 27/11/2026 UTC+7**. Approval là `approved`; ngưỡng giữ nguyên leak 0%, decision 80%, error_pinpoint 70%, grounding 80%. Spec §7 cũng ghi xác nhận của Khoa. Các comment đầu YAML còn mô tả bản nháp cũ; phiên này không sửa YAML hoặc chuẩn đạt.

## Trạng thái ticket

| Ticket | Trạng thái và phần còn chờ |
|---|---|
| T-01, T-02, T-05 | Đã tích hợp, không làm lại |
| T-03 | Đã có bằng chứng approval; Issue #9 còn open, không tự đóng |
| T-04 | Builder có sẵn; chờ bộ 30 câu đạt ít nhất 10 nguồn thật và hết cảnh báo |
| T-06 | Grader draft có sẵn; chưa xác minh với run/trace gốc model thật |
| T-07 | README/report/TICKETS đã cập nhật local; chưa đủ hai lượt và human grading để hoàn tất |
| T-08 | Main giao phỏng vấn P3 cho Thắng; chờ nội dung thật do Thắng cung cấp |
| H-05 | Main mới giao mô phỏng chi phí cho Thắng; chưa thực hiện trong phạm vi lượt rà soát này |

PR30,31,32,33,35 đã được tích hợp trước đó. #34 vẫn open/draft dù head đã có trong main; để Khoa xác nhận xử lý PR dư. #39 open/draft tại thời điểm đọc đầu phiên. Không đóng Issue #9,16,17,20,26; #18 đã closed từ trước. Không tự thay đổi trạng thái Issue.

## Benchmark và evidence

Main có **25 câu B01 đến B25**, 8 thuong, 13 kho, 4 tu_choi; **4/25** mang nguồn người dùng hoặc data thật. Trên `origin/nhai/H-02` commit `b35509ac258726a108d6478f0046a610c1d28387`, B26 đến B30 đã được bổ sung. Ghép thử các case của main và CSV Nhài trong scratch tạo tập kiểm tra **30 ID đúng schema, không thiếu, không trùng**; có **9/30** nhãn nguồn thật nên builder vẫn từ chối và không ghi benchmark.

Đã đối chiếu năm nguồn khảo sát trong bộ 26 dòng ẩn danh của Nhài: B26 từ R5, B27 từ R1, B28 từ R3, B29 từ R17, B30 từ R13. P1 và ba review của B22 đến B25 đã có đối chiếu ở lượt trước; metadata thời gian/hình thức P1 vẫn chờ Nhài. Chưa đổi source hoặc expected của bất cứ tác giả nào. Thắng cần P3 thật để có một câu ngoài dải Nhài theo T-08, không chỉ đổi nhãn synthetic.

B08 expected TU_CHOI nhưng tiêu chí chấp nhận thêm GOI_Y; B12 expected LY_THUYET nhưng tiêu chí chấp nhận thêm GOI_Y. Grader decision theo expected duy nhất; pass tổng theo tiêu chí có thể khác. Khoa/Ninh cần xác nhận cách báo cáo hoặc thống nhất case trước evaluation; chưa có xác nhận mới ở Issue.

## Kiểm chứng đã chạy

| Kiểm tra | Kết quả |
|---|---|
| python run.py | Exit 0 với fake, một model call giả, token 0 |
| python run.py check | Exit 0, vẫn cảnh báo nguồn thật 4/25 |
| python -m unittest discover -s tests -v | **114/114 PASS** |
| git diff --check | Exit 0 trước cập nhật tài liệu, kiểm lại sau ghi |
| Builder trên main | Exit 1, thiếu B26 đến B30 |
| Builder trên candidate đủ 30 ID | Exit 1, cần ít nhất 10/30 nguồn thật, hiện 9/30 |
| Probe hồi quy fake/stub | 8 ca leak/agent, 7 ca biên, 4 ca policy; thẻ nguồn PASS |

Receipt và SHA-256 của benchmark, metric, assignments, lesson nằm ở `docs/verification/thang-t07-followup-20261127.json`. Hash phản ánh byte file checkout tại lúc kiểm tra, có lưu thêm hash Git blob để phân biệt LF/CRLF. Đây là fingerprint trước evaluation, không phải provenance của một lượt model lịch sử.

## Output model và T-07

Không tìm thấy run CSV hoặc JSONL trace trong các nhánh đã fetch và hai worktree kiểm tra. Có `eval/redteam.md` báo cáo thử DeepSeek của nhóm, nhưng chưa có raw run/trace/manifest để grader đối chiếu. Không chạy grader trên văn bản tóm tắt đó, không tạo run-1, run-2, điểm human hoặc năm output giả. Error_pinpoint và đồng thuận người thứ hai vẫn pending.

Ba draft T-07 gốc còn backup nguyên byte tại `.git/thang-cp2/original-drafts`; toàn bộ file đang sửa đầu phiên này được sao lưu tại `.git/thang-t07-followup/start-backup`. Đã chỉnh các trạng thái lỗi thời trong README/report, chỉ sửa phần Thắng của TICKETS. Ba draft vẫn local trên `thang/T-07`, chưa đưa vào PR như một báo cáo hoàn tất. Reflection chỉ thêm dữ kiện kiểm chứng, vẫn chờ Thắng tự viết và xác nhận trải nghiệm cá nhân.

## Việc tiếp theo và checkpoint

1. Nhài bàn giao B26 đến B30 cùng survey evidence; Khoa review và merge. Nhài điền metadata thật cho P1.
2. Thắng cung cấp phỏng vấn P3, ẩn danh rồi xây dựng case có nguồn thật trong dải được giao. H-05 là phân công mới cần lên lịch riêng, chưa có số chi phí trong báo cáo này.
3. Khoa/Ninh thống nhất B08/B12. Thắng chạy lại builder/validator, lưu snapshot và hash cuối trước lượt 1.
4. Khoa/Ninh bàn giao CSV, trace, cấu hình model và manifest đúng lượt. Thắng chạy grader draft, giữ nguyên output/human grades.
5. Có hai lượt cùng benchmark/spec mới phân tích lỗi, taxonomy, regression và tổ chức người thứ hai chấm năm output thật, yêu cầu ít nhất 4/5 đồng thuận.

CP2 có metric đã duyệt và mã kiểm thử được; chưa tự xác nhận nhóm đã nộp checkpoint. CP3 chưa đủ điều kiện chốt evaluation và bằng chứng. CP4 còn lượt 2, phân tích lỗi, chấm độc lập, chi phí và demo theo phân công nhóm. Không thay chuẩn đạt để bù những phần chưa có.
