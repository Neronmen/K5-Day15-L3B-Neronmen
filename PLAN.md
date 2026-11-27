# Kế hoạch nhóm Neronmen: MinutesStudy Tutor

> **Việc của từng người nằm ở [TICKETS.md](TICKETS.md).** File này chỉ là bức tranh chung và các mốc.
> Nộp checkpoint ở https://ai20k-hackathon.pages.dev/#submit, **Khoa nộp sớm 15 phút**.

## Đề tài một câu

**Track F.** Học sinh THPT bí bài Toán ở nhà thì chép lời giải từ app giải bài. Gia sư MinutesStudy, khi bài còn hạn, **chỉ ra bước sai và gợi ý bước tiếp, không đưa đáp án**, chỉ dùng tài liệu giáo viên đã đăng.

**Lát cắt:** một học sinh · hỏi về một bài tập còn hạn, kèm bước làm · AI quyết định *gợi ý bước sai* / *trả lời lý thuyết kèm trang* / *nói "không có trong bài"* · học sinh tự làm ra.

**Ba điều KHÔNG làm trong phần được chấm:** không đọc ảnh vở (chỉ văn bản) · không chấm điểm · không đo các tính năng LMS khác (đăng nhập, thông báo, lịch, chấm bài).

## Ba tầng: chấm gì, demo gì, kể gì

| Tầng | Gồm | Vì sao |
|---|---|---|
| **1. Phần được chấm** (bắt buộc) | Một quyết định của gia sư, chạy qua `run.py eval` / `simulate`: bộ câu thử, metric, lượt 1 → 2, chi phí | Rubric chấm "quyết định và bằng chứng, không chấm độ hoành tráng" |
| **2. Sân khấu demo** (nên có) | Web MinutesStudy nằm ở `app/`. Chạy chính quyết định đó (app gọi chung lõi `codebase/`) trong web: giáo viên giao bài → học sinh hỏi → gợi ý / từ chối → giáo viên xem lịch sử hỏi (ticket N-08) | Giám khảo thấy sản phẩm thật, không thêm quyết định AI nào phải đo |
| **3. Lộ trình** (chỉ trên slide) | AI chấm bài ảnh có giáo viên duyệt, trợ lý giáo viên, thông báo, lịch học | "Có trong sản phẩm, chưa đo trong bộ câu thử" |

Tầng 2 chỉ làm **sau khi tầng 1 chạy xong lượt 1**.

## Luồng (workflow cố định) — khung đã chạy được với AI giả

```
input JSON {assignment_id, role, asked_at, message}
  → get_assignment → get_tutor_mode (code: hint / answer theo giờ máy chủ)
  → search_lesson (BM25 không dấu, lọc lớp) → không liên quan → KHONG_CO, không gọi model
  → call_model (SYSTEM theo chế độ, tin nhắn ở vai user)
  → citations (bỏ thẻ nguồn bịa) → check_leak (code) → lộ: sinh lại 1 lần → vẫn lộ: câu cố định
```

## Soát theo rubric (cập nhật 27/11 ~17:50) — mục tiêu: ĐẠT GIẢI

**4 điều kiện cứng để được xét giải** (thiếu 1 là loại): ✅ bản chạy thử gọi AI thật (DeepSeek, `eval --try` có token) · ⏳ bằng chứng pain ≥1 nguồn đạt ngưỡng · ⏳ ≥20 câu thử + % đạt (đã 21 câu, chờ lượt 1) · ⏳ slide

| Khối | Điểm | Đã có | Còn thiếu → ai |
|---|---|---|---|
| R1 Bằng chứng pain | 14 | form khảo sát chính thức (link trong `evidence/survey/questions.md`), kịch bản phỏng vấn, cách đếm review viết trước | **≥20 câu trả lời** + `results.csv` + `analyze_survey.py` → Nhài · **≥3 phỏng vấn**: P1 Nhài ✅ · P2 Ninh · P3 Thắng · P4 Khoa (tối 27/11) · đếm review `reviews_labeled.csv` → Nhài · `evidence/summary.md` (≥5 trích nguyên văn) → Nhài |
| R2 Impact | 11 | `spec.md` §1–§2: pain không chữ AI, bảng 3 hướng + lý do loại, công thức impact | điền **số thật** từ khảo sát vào §1, §2 → Khoa (sáng T7) |
| R3 Giải pháp AI | 16 | §4 sơ đồ, workflow cố định + lý do, 7 công cụ, chặn rủi ro 3 lớp, 4 nguyên tắc (có G10); code chạy thật; README có lệnh chạy; red-team 10/10 | — (giữ nguyên, chỉ cập nhật nếu đổi code) |
| R4 Câu thử + metric | 14 | 21 câu (≥5 kho, 4 tu_choi gồm 2 tấn công), 4 metric, DATA_CARD, `eval/README.md` §1–3 | **≥1/3 câu từ người dùng thật** (B22–B30) → Nhài · ✅ chuẩn đạt đã chốt 18:07 · người thứ 2 chấm 5 output → Thắng |
| R5 Báo cáo đánh giá | 8 | bộ chấm nháp `auto_grade.py`, ứng viên cải tiến lượt 2 (B16: tính Δ bằng code) | lượt 1 → nhóm lỗi → 1 cải tiến → lượt 2 → `eval/report.md` → Ninh + Thắng (T7) |
| R6 Chi phí | 12 | khung `cost/`, token thật ~1.600 vào / 300 ra mỗi câu | `personas.yaml` (số từ khảo sát câu 5) → `simulate` ≥50 phiên → `cost-estimate.md` 3 kịch bản, ≥2 model, giá có link → **Thắng** (T7, nhận từ Nhài) |
| R7 Slide + demo | 10 | web demo đã chạy trên mạng, câu chuyện red-team A7 (model bị lừa, code chặn) | slide 8 trang, video 30s (CP3), video dự phòng, tập trả lời 4 câu hỏi → Khoa + Ninh |
| Bonus người dùng thử | +5 | — | 2–3 học sinh dùng thử web → `validation/log.md` → **Ninh** (T7, nhận từ Nhài) |

## Mốc

| Mốc | Hạn nộp | Phải có |
|---|---|---|
| **CP1** | 17:00 T6 (nộp 16:45) | TEAMS.md ✅ · canvas 7 dòng + thẻ đề · lab coach đã xem thẻ đề · link repo ✅ |
| **CP2** | 19:30 T6 (nộp 19:15) | canvas + "đã đổi gì" · `spec.md` §4 có sơ đồ · ≥10 câu thử · metric_spec · DATA_CARD · **chuẩn đạt bằng số (khoá)** · `python run.py` chạy với AI giả |
| **CP3** | 10:00 T7 (nộp 09:45) | bằng chứng đạt ngưỡng + ≥5 trích dẫn · 20–30 câu thử (≥5 kho, ≥2 tu_choi) · video 30 giây AI thật · lượt 1 x/N + run ID · spec §0–§7 |
| **CP4** | 14:30 T7 (nộp 14:15) | lượt 1 → lượt 2 · chi phí / task thành công + tên model · slide · video dự phòng |
| **Hạn chót** | 23:59 T7 | changelog §10 · reflection mỗi người |

## ⚠️ Luật dễ mất điểm
1. **Không commit API key** (để trong `.env`). Bị phát hiện → −10.
2. **Không sửa chuẩn "đạt" sau CP2**, không xoá câu thử trượt, không sửa `expected` cho khớp output.
3. Mỗi người phải **giải thích được phần có tên mình**. Ninh giải thích phần `app/` và lõi gia sư cho cả nhóm trước CP3.
4. Không dùng bài làm, ảnh vở, tên trường thật của học sinh. Dữ liệu chạy thử đều tự dựng.
