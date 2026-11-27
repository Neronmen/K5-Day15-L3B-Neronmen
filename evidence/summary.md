# Tổng hợp bằng chứng pain

> Điền ở guide bước 1.2, xong trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Ba nguồn ngang nhau — tối thiểu **≥1 nguồn đạt ngưỡng**. Mạnh nhất: đào data ra insight → hỏi người dùng để kiểm lại (hoặc ngược lại).

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ 149 review Google Play, script `fetch_reviews.py` + `count_reviews.py`, 7 ví dụ | `evidence/data-mining.md` |
| Phỏng vấn (≥3 người ngoài nhóm, đúng người dùng) | ☐ | `evidence/interviews/P1.md`… |
| Khảo sát (≥20 người ngoài nhóm, đúng người dùng) | ☑ n = 22 học sinh lớp 10–12 (xuất lúc 18:09 27/11) | `evidence/survey/` |

## 2. Số chính

- Đào data: trong 19/149 review Google Play có nói về cách dùng lời giải (Photomath, QANDA, AI Hay), **11/19 (58%) là dùng để lấy đáp án / giải hộ**, 8/19 dùng để hiểu bài. n nhỏ: 87% review chỉ chê lỗi app hoặc chuyện tiền.
- Phỏng vấn: 1/1 người đã phỏng vấn gặp pain (P1, gia sư Toán; cần ≥3) *(n nhỏ không ghi %)* · số lần / tháng: P1 không hỏi, P2 __, P3 __ · P1 mất 40–50 phút / tuần rà bài cho 2 học sinh
- Khảo sát (học sinh lớp 10–12, ngoài nhóm; `evidence/survey/results.csv`, đếm bằng `analyze_survey.py`): n = 22 · **chép gần như nguyên lời giải 10/22 (45%)** — dưới ngưỡng 50% · trong 10 em chép, **8/10 chỉ làm được một phần hoặc không làm được bài kiểm tra cùng dạng** · lần đó đã hỏi ChatGPT / chatbot 16/22, chụp lên app giải bài 11/22 · dùng app / chatbot ≥6 lần / tuần 14/22 · lý do: sai mà không biết sai ở đâu 10/22, quá nhiều bài 10/22, không biết bắt đầu từ đâu 9/22, chỉ cần nộp cho đủ 2/22 (chọn nhiều) · chọn "quá nhiều bài" hoặc "chỉ cần nộp cho đủ" 11/22 (đúng một nửa)

Phỏng vấn nhiều vai thì đếm theo từng vai, không cộng chung.

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | gia sư Toán, kèm 2 HS lớp 11 | Có (lần cụ thể 25/11) | không hỏi | 40–50 phút / tuần rà bài tìm chỗ hổng | bắt làm lại tại chỗ + nhờ phụ huynh thu điện thoại |
| P2 | | | | | |
| P3 | | | | | |

## 3. ≥5 trích dẫn hoặc ví dụ nguyên văn (có nguồn, bỏ tên)

1. "App hay quá, chụp ảnh là có ngay đáp án" — review QANDA 5★, dòng data 81 (`reviews_labeled.csv`)
2. "nó không giải mà là nó lấy đáp án giống chứ không giải, nên khi cô cho mấy bài khác đi là coi như vô dụng" — review QANDA 4★, dòng data 52
3. "Rat hieu ich ,cho dap an phe qua" — review Photomath 5★, dòng data 48
4. "Hôm sau mình đổi số và cho làm lại ngay một câu lượng giác tương tự trong 10 phút đầu giờ thì bạn ấy chỉ viết được mỗi dòng chép lại đề bài rồi bỏ giấy trắng" — P1 (gia sư Toán)
5. "Cách này chỉ giải quyết được lúc có mặt mình ở đó, còn 5 ngày còn lại trong tuần mình không ngồi cạnh được" — P1
6. "Em đã chụp ảnh lên Chatgpt, sau đó chép vào vở, nhưng em vẫn bị cô giáo mắng vì đáp án bị sai." — phiếu khảo sát R3
7. "nhìu bài muốn tư duy nhưng tra là ra lun đáp án" — phiếu khảo sát R17
8. "Hóa rất khó đối với em mà cô giáo cho toàn bài khó, nhiều công thức hóa học em không biết nên bắt đầu từ đâu khi giải bài" — phiếu khảo sát R5

## 4. Các nguồn có khớp nhau không

Data (review) nói: trong số người nhắc tới cách dùng, đa số dùng app để lấy đáp án (11/19), và có người tự thấy lời giải tra được vô dụng khi gặp bài khác (dòng 52); không cho biết hậu quả ở bài kiểm tra. Người dùng nói: khảo sát 10/22 chép gần như nguyên, 8/10 trong số đó hổng bài kiểm tra cùng dạng; gia sư P1 kể một lần cụ thể học sinh chép rồi bỏ giấy trắng khi đổi số. Khớp / lệch ở đâu, vì sao: **khớp hướng** — cả review, khảo sát và P1 đều cho thấy lời giải có sẵn được dùng để chép / lấy đáp án và không giúp làm bài khác. **Lệch:** (1) học sinh dùng ChatGPT (16/22) nhiều hơn app giải bài (11/22); (2) 3/6 câu kể ở câu 9 là môn Lý / Hoá (2/6 là Toán), ví dụ của P1 là lượng giác lớp 11, trong khi lát cắt chỉ làm phương trình bậc hai Toán 10.

## 5. Kết luận

Giả thuyết ở `evidence/hypothesis.md`: **sai một phần** — theo luật đọc ghi trước ở `evidence/survey/questions.md`: (1) chép gần như nguyên 10/22 (45%) **không đạt** ngưỡng ≥50%; (2) trong số em chép, 8/10 hổng bài kiểm tra cùng dạng — **đạt** ngưỡng ≥40%; (3) 11/22 chọn "quá nhiều bài" hoặc "chỉ cần nộp cho đủ" — đúng một nửa, gợi ý từng bước không giải quyết được nhóm này. *Quan sát thêm, không thuộc luật đọc:* 5/22 "chỉ xem đáp số để so" và 4/22 "xem gợi ý một bước rồi tự làm" — tức nhiều em không chép nguyên nhưng vẫn dựa vào lời giải có sẵn; "sai mà không biết sai ở đâu" 10/22 khớp đúng việc lát cắt làm. Điều vẫn chưa biết: pain ở Toán có nặng bằng Lý / Hoá không; phỏng vấn mới có 1/3 người. **Cần nhóm quyết định** có thu hẹp người dùng (em muốn tự làm nhưng không biết sai ở đâu) và ghi vào canvas / spec §10.

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| | | |
