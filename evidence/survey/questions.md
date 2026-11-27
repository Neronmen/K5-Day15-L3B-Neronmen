# Khảo sát: "Lần gần nhất em gặp bài tập khó ở nhà"

- **Đối tượng:** học sinh THPT (lớp 10–12), **ngoài nhóm**. Mục tiêu ≥20 người, tốt nhất ≥30.
- **Kênh gửi:** em, cháu, con của thành viên và đồng nghiệp; nhờ phụ huynh quen chuyển vào nhóm Zalo phụ huynh; nhờ giáo viên / gia sư quen gửi học sinh. Ghi kênh thật đã gửi: ____
- **Mở lúc:** 14:50 27/11/2026 — **form chính thức là form của Nhài** (tạo bằng `create_form.gs`), cả nhóm chỉ gửi link này: https://docs.google.com/forms/d/e/1FAIpQLSd6bRMF8Y8Cd-G3xis1M9toEj7V98FB5WFF-wzwVpEu0D4ODw/viewform · Form thử của Khoa (mở 14:43) đã **ngừng nhận câu trả lời**; câu trả lời đã có ở form đó (nếu có) xuất riêng, ghi rõ trong `results.csv`, không gộp lẫn · **Chốt lúc:** ____ (chốt trước 08:00 Thứ Bảy 28/11 để kịp CP3)
- **Đếm:** `python evidence/survey/analyze_survey.py anonymize evidence/survey/raw-<ngay>.csv` → `results.csv`, rồi `python evidence/survey/analyze_survey.py` (đếm đúng luật ở mục "Cách đọc kết quả")
- **Không thu** tên, số điện thoại, tên trường, lớp cụ thể. Người trả lời là trẻ vị thành niên: form ghi rõ ẩn danh, chỉ hỏi hành vi, **không phán xét** việc dùng app.
- Xuất kết quả thành `results.csv` (đã xoá cột nhận diện). Bản gốc đặt tên `raw-*.csv`, không commit.

## Lời mở đầu (dán vào mô tả Google Form)

> Chào em! Nhóm anh chị đang tìm hiểu cách các bạn học sinh làm bài tập ở nhà. Form khoảng 2 phút, hoàn toàn ẩn danh, không hỏi tên hay trường. Không có câu trả lời đúng hay sai, em cứ trả lời thật nhé. Cảm ơn em!

## Câu hỏi (chép nguyên văn sang Google Form)

| # | Câu hỏi | Kiểu trả lời |
|---|---|---|
| 1 | Em đang học lớp | 10 · 11 · 12 · Khác (→ cảm ơn, kết thúc) |
| 2 | Lần gần nhất em gặp một bài tập về nhà mà **không tự làm được** là khi nào? | Hôm nay / hôm qua · Trong tuần này · Tuần trước · Lâu hơn · Chưa bao giờ |
| 3 | Lần đó em đã làm gì? | Chọn nhiều: Chụp ảnh lên app giải bài · Hỏi ChatGPT / chatbot · Tìm lời giải trên mạng · Hỏi bạn · Hỏi bố mẹ, anh chị · Hỏi thầy cô / gia sư · Xem lại vở, sách · Bỏ qua bài đó |
| 4 | Nếu đã dùng app / chatbot / mạng: em đã dùng lời giải đó thế nào? | Chọn **một**: Chép gần như nguyên vào bài · Đọc hiểu rồi tự viết lại · Chỉ xem đáp số để so · Xem gợi ý một bước rồi tự làm · Không dùng |
| 5 | Trong **1 tuần qua**, em dùng app giải bài / chatbot cho bài tập về nhà khoảng mấy lần? | 0 · 1–2 · 3–5 · 6–10 · Trên 10 |
| 6 | Lần gần nhất có bài kiểm tra **cùng dạng** với bài em đã xem lời giải, em làm được không? | Làm được hết · Làm được một phần · Không làm được · Chưa có bài kiểm tra như vậy |
| 7 | Vì sao em dùng lời giải có sẵn thay vì tự làm tiếp? | Chọn nhiều: Không biết bắt đầu từ đâu · Làm sai mà không biết sai ở đâu · Quá nhiều bài, không đủ thời gian · Không có ai để hỏi lúc đó · Chỉ cần nộp cho đủ · Khác |
| 8 | Nếu có người chỉ cho em **bước nào sai** và **gợi ý bước tiếp** (không đưa đáp án), em có muốn tự làm tiếp không? | Có · Tuỳ bài · Không, em muốn có đáp án luôn |
| 9 | Kể ngắn lần gần nhất em bí một bài ở nhà (môn gì, bí ở đâu, em đã làm gì) | Đoạn văn (không bắt buộc, đừng ghi tên người hay trường) |

## Cách đọc kết quả (ghi trước khi xem kết quả)

- **Mẫu số chính:** số học sinh lớp 10–12 trả lời.
- **Giả thuyết đúng** nếu ≥50% chọn câu 4 = "Chép gần như nguyên" hoặc câu 5 ≥ "1–2" có kèm câu 4 = "Chép…", **và** trong số người chép, ≥40% chọn câu 6 = "Một phần" hoặc "Không làm được".
- Câu 7 cho biết lý do: nếu "Quá nhiều bài" hoặc "Chỉ cần nộp cho đủ" chiếm đa số → giả thuyết sai một phần (gợi ý từng bước không giải quyết được).
- Câu 8 là câu thái độ, chỉ để tham khảo, **không dùng làm bằng chứng pain**.
- Câu 5 → số lần / tuần, dùng cho persona chi phí.
- Câu 9 → trích nguyên văn (bỏ tên) vào `evidence/summary.md`, và làm nguồn câu thử (`source = nguoi_dung: khao_sat R5` — `run.py check` chỉ nhận mã `nguoi_dung / data_that / tu_viet / sinh_seed`, nên **không** ghi `khao_sat: …` ở đầu).
