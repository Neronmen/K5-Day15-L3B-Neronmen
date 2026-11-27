# Đào data — cách đếm và kết quả

> Điền ở guide bước 1.2. Ôn lại: ngày 2, ngày 6 · lab ngày 2, lab ngày 6.
> Không đào data thì xoá file này. Script / công thức đếm để trong repo (vd `evidence/count.py` hoặc ghi công thức Sheets ngay dưới), người khác chạy lại phải ra cùng số.
> Repo chỉ chứa số đã tổng hợp và vài dòng ví dụ — không chép lại nguyên file data.

## 1. Cách đếm — viết TRƯỚC khi chạy

*(Viết lúc _16_:_48_ 27/11/2026, trước khi đọc review nào.)*

- Data dùng: review công khai trên Google Play của 2–3 app giải bài bằng ảnh: photomath(https://photomath.com/install/) · QANDA(https://play.google.com/store/apps/details?id=com.mathpresso.qanda&hl=vi) · AI Hay(https://play.google.com/store/apps/details?id=com.hay1.tintuc&hl=vi) (27/11/2026). Cách chọn app: các app hiện ra đầu tiên khi tìm "giải bài tập bằng ảnh" trên Google Play, có ≥10.000 lượt tải và có review tiếng Việt.
- Đếm gì: review tiếng Việt nhắc tới **cách dùng lời giải**, gắn tay một trong 3 nhãn:
  - `giai_ho`: khen app giải hộ, chép bài, nộp bài nhanh, "không cần học"
  - `hieu_bai`: dùng để hiểu cách làm, xem từng bước, kiểm tra lại bài đã tự làm
  - `khac`: lỗi app, quảng cáo, giá tiền, khen chung chung không nói cách dùng
- Trên tập nào: mỗi app lấy **~50 review tiếng Việt mới nhất** (sắp xếp "Gần đây nhất"), theo thứ tự hiện ra, không chọn lọc. Lọc: bỏ review không phải tiếng Việt và review chỉ có emoji hoặc 1–2 chữ.
- **Mẫu số là gì:** (a) tất cả review đã đọc sau khi lọc; (b) chỉ các review nói về cách dùng (`giai_ho` + `hieu_bai`). Báo cả hai, kết luận chính dùng (b).
- Script / công thức: `python evidence/count_reviews.py` đọc `evidence/reviews_labeled.csv` (cột `id, app, ngay, so_sao, trich, nhan, ghi_chu`). Mỗi review trích ≤2 câu, **không chép tên người viết**.
- Giới hạn biết trước: người viết review không chắc là học sinh THPT; review hay lệch về hai đầu 1 sao / 5 sao.

## 2. Đọc trước, đếm sau

Lấy bằng `python evidence/fetch_reviews.py` (27/11/2026): mỗi app lấy 50 review đầu tiên qua bộ lọc, trong lượt 200 review mới nhất tải về → 150 review. Bỏ 1 review tiếng Pháp (dòng 23, theo luật lọc) → **149 review**. Khoảng thời gian: Photomath 12/2025–10/2026 · QANDA 07–11/2026 · AI Hay 17–26/11/2026.

Các *kiểu* nội dung thấy khi đọc:
- Đa số chê lỗi kỹ thuật: khung chụp nhỏ, không nhận ảnh, giải sai, load lâu (Photomath, QANDA).
- Chuyện tiền: nạp tiền không được giải, không huỷ được gói, bị trừ "sao" mỗi lượt hỏi (QANDA, AI Hay).
- Khen app **cho đáp án / giải nhanh**: "chụp ảnh là có ngay đáp án", "cho đáp án phê quá".
- Ít hơn: khen **giải thích / phân tích / dễ hiểu**, hoặc chê giải thích khó hiểu.
- AI Hay chủ yếu được dùng như chatbot chung (chat với nhân vật, làm văn, hỏi đáp), ít review nói về bài Toán.

## 3. Kết quả

Nhãn: AI gợi ý (cột `nhan_ai`), Nhài duyệt và quyết định 11 dòng chưa chắc (cột `nhan`, lý do ở `ghi_chu`). Khớp AI 144/149, Nhài đổi 5 dòng: 4, 15, 20, 69, 102.

| Đếm gì | x / N | % | Ghi chú |
|---|---|---|---|
| Review nói về cách dùng lời giải (`giai_ho` + `hieu_bai`) | 19/149 | 13% | 87% còn lại là lỗi app, tiền, khen chung |
| **`giai_ho` trong số review nói về cách dùng** | **11/19** | **58%** | mẫu số (b) — kết luận chính |
| `hieu_bai` trong số review nói về cách dùng | 8/19 | 42% | |
| `giai_ho` trên tất cả review | 11/149 | 7% | mẫu số (a) |
| Theo app — `giai_ho` / nói về cách dùng | Photomath 2/5 · QANDA 8/10 · AI Hay 1/4 | — | n từng app rất nhỏ, không so % giữa app |

Ghi dạng "x/N (y%)". "Nhiều bạn…" không phải số.

## 4. ≥5 ví dụ cụ thể (mã dòng trong `reviews_labeled.csv`, nguyên văn, không tên người viết)

1. Dòng 81 · QANDA · 5★ · `giai_ho`: "App hay quá, chụp ảnh là có ngay đáp án"
2. Dòng 48 · Photomath · 5★ · `giai_ho`: "Rat hieu ich ,cho dap an phe qua"
3. Dòng 52 · QANDA · 4★ · `giai_ho`: "nó không giải mà là nó lấy đáp án giống chứ không giải, nên khi cô cho mấy bài khác đi là coi như vô dụng"
4. Dòng 100 · QANDA · 4★ · `giai_ho`: "có những bài ko có trên google thì lại thấy trên này"
5. Dòng 37 · Photomath · 5★ · `hieu_bai`: "hay quá còn có chỉ bài đẫ lm"
6. Dòng 38 · Photomath · 4★ · `hieu_bai`: "giải thích hơi khó hiểu"
7. Dòng 69 · QANDA · 5★ · `hieu_bai`: "chỉ cần chụp cái xong nó tự giải mà còn phân tích cho nữa"

## 5. Giới hạn của data

Data cho biết người ta **làm gì**, không cho biết **vì sao**. Thiếu gì, lệch về phía nào:
- Chỉ 19/149 review nói về cách dùng → n nhỏ, % dao động mạnh nếu đổi vài nhãn.
- Không biết người viết có phải học sinh THPT không (dòng 62 tự nhận lớp 9).
- Review lệch về 1★ / 5★, đa số chê lỗi kỹ thuật, không nói chuyện học.
- AI Hay là chatbot đa năng, không hẳn "app giải bài bằng ảnh" như luật chọn app đã ghi → kéo tỉ lệ "nói về cách dùng" xuống.
- Review **không** nói được hậu quả (có làm được bài kiểm tra cùng dạng không) — dòng 52 là ví dụ duy nhất gần ý này.

→ Kiểm lại bằng khảo sát câu 4 (chép nguyên hay đọc hiểu) và câu 6 (kiểm tra cùng dạng), và phỏng vấn giáo viên câu 2–3 (`evidence/interviews/kich-ban.md`).
