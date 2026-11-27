# Reflection — Phùng Thị Nhài

> ⚠️ BẢN NHÁP do Claude Code soạn từ lịch sử commit. Nhài đọc lại, viết lại bằng lời của mình, điền câu 3 sau khi có lượt chạy, rồi xoá dòng này. Hạn 23:59 Thứ Bảy 28/11.

1. **Vai trò + phần mình làm:** Thành viên phụ trách bằng chứng pain (R1): `evidence/`, câu thử B22–B30. Chi phí (H-05) và người dùng thử (H-06) được chuyển cho Thắng và Ninh lúc 18:08 27/11.
   - H-01: tạo Google Form khảo sát từ `evidence/survey/questions.md` bằng `evidence/survey/create_form.gs`, mở 14:50 27/11.
   - H-02: lấy 150 review Google Play (Photomath, QANDA, AI Hay) bằng `evidence/fetch_reviews.py`, duyệt nhãn 149 review, đếm bằng `evidence/count_reviews.py` → 11/19 review nói về cách dùng là dùng để lấy đáp án (`evidence/data-mining.md`). Commit `891e3bb`, `0854704`.
   - `evidence/survey/analyze_survey.py` để ẩn danh và đếm khảo sát theo luật đọc đã ghi trước.
   - H-03: 9 câu thử B22–B30, đều nguồn thật: B23–B25 viết lại từ review (`data_that`), B22 và B26–B30 viết lại từ câu 9 khảo sát (`nguoi_dung: khao_sat R_`) — `eval/cases/nhai.csv`, PR #41, #43.
   - H-04: khảo sát n = 26 học sinh lớp 10–12 (`evidence/survey/results.csv` đã ẩn danh); chép gần như nguyên 14/26, trong đó 12/14 hổng bài kiểm tra cùng dạng; kết luận "đúng nhưng sát ngưỡng" (ở n = 22 chỉ 10/22) — `evidence/summary.md`, PR #42, #44. Persona chi phí theo câu 5 khảo sát trong `cost/personas.yaml`.
   - Gỡ phỏng vấn P1 khỏi repo (PR #44) vì không xác minh được thời điểm phỏng vấn; thay B22 bằng câu từ khảo sát R26.

2. **AI hỗ trợ mình thế nào:** Dùng Claude Code (Claude Opus 5.5) để viết các script Python / Apps Script và gợi ý nhãn review. Chỗ phải sửa lại output AI:
   - AI gợi ý nhãn cho 149 review, mình đổi 5 nhãn (dòng 4, 15, 20, 69, 102), ví dụ dòng 102 "lm văn hay" AI gán `giai_ho` nhưng không phải môn Toán nên đổi `khac`.
   - Link form AI chép lại từ ảnh chụp bị sai một ký tự (`l` thành `1`), phải lấy lại link gốc trong Google Form.
   - Script lấy review ban đầu in sai số review đã đọc ("đọc 200"), đã sửa.
   - AI viết câu thử từ câu kể khảo sát; mình duyệt từng câu trước khi ghi (B22–B30).
   - AI nhắc phải ghi cả kết quả n = 22 (dưới ngưỡng) bên cạnh n = 26, không chỉ ghi số đẹp.
   - __ (tự thêm bằng lời của mình)

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:** __ (điền sau khi có `eval/run-1.csv` đã chấm)
