# Reflection — Phùng Thị Nhài

> ⚠️ BẢN NHÁP do Claude Code soạn từ lịch sử commit. Nhài đọc lại, viết lại bằng lời của mình, điền câu 3 sau khi có lượt chạy, rồi xoá dòng này. Hạn 23:59 Thứ Bảy 28/11.

1. **Vai trò + phần mình làm:** Thành viên phụ trách bằng chứng và chi phí (`evidence/`, `cost/`, `validation/`, câu thử B22–B30).
   - H-01: tạo Google Form khảo sát từ `evidence/survey/questions.md` bằng `evidence/survey/create_form.gs`, mở 14:50 27/11.
   - H-02: lấy 150 review Google Play (Photomath, QANDA, AI Hay) bằng `evidence/fetch_reviews.py`, duyệt nhãn 149 review, đếm bằng `evidence/count_reviews.py` → 11/19 review nói về cách dùng là dùng để lấy đáp án (`evidence/data-mining.md`). Commit `891e3bb`, `0854704`.
   - `evidence/survey/analyze_survey.py` để ẩn danh và đếm khảo sát theo luật đọc đã ghi trước.
   - __ (H-03 câu thử, H-04 tổng hợp, H-05 chi phí, phỏng vấn P_: điền khi xong)

2. **AI hỗ trợ mình thế nào:** Dùng Claude Code (Claude Opus 5.5) để viết các script Python / Apps Script và gợi ý nhãn review. Chỗ phải sửa lại output AI:
   - AI gợi ý nhãn cho 149 review, mình đổi 5 nhãn (dòng 4, 15, 20, 69, 102), ví dụ dòng 102 "lm văn hay" AI gán `giai_ho` nhưng không phải môn Toán nên đổi `khac`.
   - Link form AI chép lại từ ảnh chụp bị sai một ký tự (`l` thành `1`), phải lấy lại link gốc trong Google Form.
   - Script lấy review ban đầu in sai số review đã đọc ("đọc 200"), đã sửa.
   - __ (tự thêm)

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:** __ (điền sau khi có `eval/run-1.csv` đã chấm)
