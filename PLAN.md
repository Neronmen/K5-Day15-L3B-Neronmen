# Kế hoạch nhóm (PM board)

> Cập nhật file này mỗi khi xong việc: đổi `[ ]` thành `[x]`. Ai kẹt **quá 20 phút** thì báo nhóm ngay, đừng ngồi một mình.
> 15 phút trước mỗi checkpoint, cả nhóm cùng kể lại câu chuyện: Pain → Impact → Giải pháp → Đánh giá → Chi phí.

## Vai trò *(tạm, chốt lại sau khi chọn đề)*

| Mã | Vai | Phụ trách chính | Cặp |
|---|---|---|---|
| Khoa (TV1) | Đội trưởng / PM | Nộp checkpoint, canvas, `spec.md` §1–2, slide, giữ mạch câu chuyện | – |
| TV2 | Evidence | Khảo sát, phỏng vấn, `evidence/` | Cặp Y |
| TV3 | AI engineer | `codebase/`, nối model, chặn rủi ro | Cặp X |
| TV4 | Eval & Cost | `eval/`, `data/DATA_CARD.md`, `cost/` | Cặp Y → X |

Nhóm 3 người: Khoa kiêm thêm việc của TV4. Nhóm 5 người: TV5 phỏng vấn + người dùng thử (bonus) + video.

## ⏰ Thứ Sáu 27/11

### Ngay bây giờ → 12:00
- [ ] **Khoa (TV1)** tạo repo public `K5-Day15-<lớp>-<TenNhom>`, push thư mục này lên, mời cả nhóm làm collaborator
- [ ] **TV2** chép `evidence/survey/questions.md` sang Google Form → **gửi lớp trước 12:00** (cần ≥20 người)
- [ ] **Mọi người** hẹn ≥1 bạn ngoài nhóm để phỏng vấn (chiều tại lớp hoặc gọi video)
- [ ] **Mọi người** điền tên + mã học viên vào `TEAMS.md` (đội trưởng ở dòng 1)

### 12:00 → 16:00
- [ ] **TV3** cài Python, chạy `python run.py` ra câu giả. Lấy API key (Gemini free / OpenAI / Claude), điền `.env`
- [ ] **TV3** dựng dữ liệu giả để chạy thử trong `data/` (có seed, ghi vào `data/DATA_CARD.md`)
- [ ] **TV4** đọc `eval/README.md`, nháp 10 câu thử đầu tiên
- [ ] **Khoa (TV1)** điền `spec.md` §1 (pain) + §2 (bảng impact ≥3 hướng)
- [ ] Mỗi người phỏng vấn xong ≥1 người → `evidence/interviews/Px.md`

### 🔴 CP1 · 17:00 (3 điểm)
- [ ] `TEAMS.md` đúng format (`python run.py check`)
- [ ] `canvas.md` đủ 7 dòng
- [ ] Bài toán 1–2 câu (không chữ AI) + lát cắt 1 câu
- [ ] Link repo mở được bằng cửa sổ ẩn danh
- [ ] **Khoa nộp lúc 16:45** ở https://ai20k-hackathon.pages.dev/#submit

### 17:00 → 19:30
- [ ] 17:00–17:20 cả nhóm tổng hợp số khảo sát + phỏng vấn đầu tiên → chốt lát cắt
- [ ] **Cả nhóm** vẽ sơ đồ kiến trúc → `spec.md` §4
- [ ] **TV3 (cặp X)**: khung `codebase/agent.py` + `tools.py` chạy với AI giả
- [ ] **TV4 + TV2 (cặp Y)**: `data/DATA_CARD.md` + ≥10 câu thử + `eval/metric_spec.yaml` (≥3 metric)
- [ ] **Cả nhóm** chốt **chuẩn "đạt" bằng số** ở `spec.md` §7. ⚠️ Từ đây KHÔNG ĐƯỢC SỬA

### 🔴 CP2 · 19:30 (4 điểm)
- [ ] Canvas + dòng "Đã đổi gì" · link `spec.md` (§4 có sơ đồ) · `benchmark.csv` ≥10 câu · metric_spec · data card · chuẩn "đạt" · `python run.py` chạy hết luồng
- [ ] **Khoa nộp lúc 19:15**

### Tối Thứ Sáu (làm ở nhà)
- [ ] **TV3**: nối model thật, **xong trước khi ngủ**. Cài chặn: không đưa lời giải, chống "bỏ qua hướng dẫn trước đó"
- [ ] **TV4 + TV2**: mở rộng 20–30 câu thử (≥5 `kho`, ≥2 `tu_choi` gồm 2 câu tấn công, ≥1/3 câu từ khảo sát / data thật)
- [ ] **TV2**: chốt khảo sát lúc 08:00 sáng mai, xuất `results.csv` đã ẩn danh

## ⏰ Thứ Bảy 28/11

### 07:30 → 10:00
- [ ] 07:30 cả nhóm họp 30 phút: chốt bằng chứng (`evidence/summary.md`, ≥5 trích dẫn) + bảng impact
- [ ] Chạy **lượt 1** cùng nhau: `python run.py eval` → chấm cột `pass` → `python run.py score`
- [ ] **TV3** quay **video 30 giây** gọi AI thật → YouTube "Không công khai", mở thử bằng cửa sổ ẩn danh
- [ ] `spec.md` có đủ §0–§7

### 🔴 CP3 · 10:00 (4 điểm). Khoa nộp lúc 09:45

### 10:00 → 13:00
- [ ] Cả nhóm ngồi chung đọc câu trượt → gom nhóm lỗi → chọn **1 cải tiến**
- [ ] **TV3**: sửa → **lượt 2** trên cùng bộ câu thử
- [ ] **TV4**: `cost/personas.yaml` (≥3 persona) → `python run.py simulate` (≥50 phiên) → `cost/cost-estimate.md` (3 kịch bản, ≥2 model, giá có link + ngày xem)
- [ ] **TV2** (bonus +5): 2–3 bạn ngoài nhóm dùng thử → `validation/log.md`
- [ ] Người thứ hai chấm thử 5 output, khớp ≥4/5 → ghi `eval/README.md`

### 13:00 → 14:30
- [ ] **Khoa (TV1)**: slide 8 trang, mỗi trang có ≥1 con số có nguồn → xuất PDF vào repo
- [ ] Quay video demo dự phòng
- [ ] Tập demo: 1 ca thường + 1 ca khó + chạy câu lạ giám khảo đưa. **Mỗi người nói 1 phần**

### 🔴 CP4 · 14:30 (4 điểm). Khoa nộp lúc 14:15
### 14:30–18:00 Demo · 🔴 23:59 hạn chót: mọi thay đổi ghi `spec.md` §10, mỗi người 1 file `reflection/`

## ⚠️ Luật dễ mất điểm
1. **Không commit API key** (để trong `.env`). Bị phát hiện → −10 điểm.
2. **Không sửa chuẩn "đạt" sau CP2**, không xoá câu thử trượt, không sửa `expected` cho khớp output.
3. **Không commit** nguyên file data BTC (`data-btc/` đã có trong `.gitignore`).
4. Mỗi người phải **giải thích được phần có tên mình**. Dùng AI vào việc gì thì ghi vào `docs/ai-usage.md`.
