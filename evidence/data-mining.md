# Đào data — cách đếm và kết quả

> Điền ở guide bước 1.2. Ôn lại: ngày 2, ngày 6 · lab ngày 2, lab ngày 6.
> Không đào data thì xoá file này. Script / công thức đếm để trong repo (vd `evidence/count.py` hoặc ghi công thức Sheets ngay dưới), người khác chạy lại phải ra cùng số.
> Repo chỉ chứa số đã tổng hợp và vài dòng ví dụ — không chép lại nguyên file data.

## 1. Cách đếm — viết TRƯỚC khi chạy

*(Viết lúc __:__ 27/11/2026, trước khi đọc review nào.)*

- Data dùng: review công khai trên Google Play của 2–3 app giải bài bằng ảnh: __ · __ · __ (link trang app + ngày xem __). Cách chọn app: các app hiện ra đầu tiên khi tìm "giải bài tập bằng ảnh" trên Google Play, có ≥10.000 lượt tải và có review tiếng Việt.
- Đếm gì: review tiếng Việt nhắc tới **cách dùng lời giải**, gắn tay một trong 3 nhãn:
  - `giai_ho`: khen app giải hộ, chép bài, nộp bài nhanh, "không cần học"
  - `hieu_bai`: dùng để hiểu cách làm, xem từng bước, kiểm tra lại bài đã tự làm
  - `khac`: lỗi app, quảng cáo, giá tiền, khen chung chung không nói cách dùng
- Trên tập nào: mỗi app lấy **~50 review tiếng Việt mới nhất** (sắp xếp "Gần đây nhất"), theo thứ tự hiện ra, không chọn lọc. Lọc: bỏ review không phải tiếng Việt và review chỉ có emoji hoặc 1–2 chữ.
- **Mẫu số là gì:** (a) tất cả review đã đọc sau khi lọc; (b) chỉ các review nói về cách dùng (`giai_ho` + `hieu_bai`). Báo cả hai, kết luận chính dùng (b).
- Script / công thức: `python evidence/count_reviews.py` đọc `evidence/reviews_labeled.csv` (cột `id, app, ngay, so_sao, trich, nhan, ghi_chu`). Mỗi review trích ≤2 câu, **không chép tên người viết**.
- Giới hạn biết trước: người viết review không chắc là học sinh THPT; review hay lệch về hai đầu 1 sao / 5 sao.

## 2. Đọc trước, đếm sau

Đã đọc __ dòng đầu và từ điển cột. Các *kiểu* hành vi thấy được (trước khi định nghĩa thứ cần đếm):
- __
- __

## 3. Kết quả

| Đếm gì | x / N | % | Ghi chú |
|---|---|---|---|
| | | | |
| | | | |

Ghi dạng "x/N (y%)". "Nhiều bạn…" không phải số.

## 4. ≥5 ví dụ cụ thể (mã dòng / mã đã ẩn danh, không đoán ai là ai)

1.
2.
3.
4.
5.

## 5. Giới hạn của data

Data cho biết người ta **làm gì**, không cho biết **vì sao**. Thiếu gì, lệch về phía nào: __
→ Kiểm lại bằng phỏng vấn / khảo sát nào: __
