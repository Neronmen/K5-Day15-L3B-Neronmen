# Tickets — Neronmen · MinutesStudy Tutor

> **Cách làm:** mỗi người làm **từ trên xuống** trong cột của mình. Xong ticket nào thì đổi `[ ]` → `[x]` và ghi giờ.
> Mỗi người **chỉ sửa file mình sở hữu** (ghi trong ticket), nên 4 người chạy song song mà không đụng nhau.
> **Đổi chữ ký hàm trong `codebase/tools.py` phải báo Khoa trước** (đó là hợp đồng giữa các phần).
> Kẹt **quá 20 phút** → nhắn group ngay.

## Quy trình Git

```bash
git clone https://github.com/Neronmen/K5-Day15-L3B-Neronmen.git
cd K5-Day15-L3B-Neronmen
git checkout -b <ten>                   # MỖI NGƯỜI MỘT NHÁNH: khoa · ninh · thang · nhai (tạo 1 lần)
git pull origin main                    # mỗi lần bắt đầu làm: lấy bản mới nhất của main về nhánh mình
# ... làm, chạy python run.py để chắc không vỡ ...
git add <file của mình> && git commit -m "N-02: BM25 không dấu cho search_lesson"   # ghi mã ticket trong message
git push -u origin <ten>                # rồi mở Pull Request <ten> → main trên GitHub
```

- **Không commit thẳng lên `main`.** Mọi thứ đi qua nhánh của mình + Pull Request.
- **Khoa review và merge.** Sát giờ checkpoint thì Khoa merge luôn, review sau. Merge xong, mọi người `git pull origin main` vào nhánh mình.
- Ghi `Closes #<số issue>` trong mô tả PR để issue tự đóng khi merge.
- Không commit `.env`, không commit API key (−10 điểm).
- Trước khi mở PR: `python run.py` chạy không lỗi.

## Cấu trúc repo

| Thư mục | Là gì | Ai sửa |
|---|---|---|
| `codebase/`, `data/`, `eval/`, `cost/` | **Lõi gia sư được đo và chấm** (khung `run.py` của BTC, chỉ thư viện chuẩn Python) | theo ticket |
| `app/` | **Web MinutesStudy** (FastAPI + Next.js): LMS cho giáo viên và học sinh, dùng làm sân khấu demo | Ninh (N-08); ai sửa giao diện thì mở PR riêng |
| `evidence/`, `validation/` | Bằng chứng, người dùng thử | Nhài + mọi người |

**Luật:** logic quyết định của gia sư chỉ viết ở `codebase/`. `app/` gọi vào đó, không viết bản thứ hai.

## Hợp đồng đã chốt (khung đã có sẵn, chạy được với AI giả)

| Phần | File | Hợp đồng |
|---|---|---|
| Input câu thử | `eval/benchmark.csv` cột `input` | JSON `{"assignment_id","role","asked_at","message"}` |
| Output | `codebase/agent.py` | dòng đầu luôn là `[QUYET_DINH: GOI_Y / LY_THUYET / KHONG_CO / GIAI / TU_CHOI]` |
| Dữ liệu | `data/lesson.json`, `data/assignments.json` | xem mẫu 3 trang + 2 bài đang có |
| Công cụ | `codebase/tools.py` | `get_assignment`, `get_tutor_mode`, `search_lesson`, `check_leak`, `citations` (chữ ký trong docstring đầu file) |
| Prompt | `codebase/prompts.py` | `SYSTEM_HINT`, `SYSTEM_ANSWER`, `NOT_FOUND` |
| Câu thử | `eval/cases/<ten>.csv` | mỗi người một file, đúng 6 cột của benchmark, đúng dải mã của mình → script ghép lại |

**Dải mã câu thử:** Khoa `B01–B06` · Ninh `B07–B13` · Thắng `B14–B21` · Nhài `B22–B30`.

---

## 👑 Khoa · Đội trưởng + Tech lead

**Sở hữu:** `codebase/agent.py`, `canvas.md`, `spec.md`, `README.md`, `slides/`, `eval/cases/khoa.csv`

- [x] **K-01 · CP1 (→ 16:45)**: duyệt `canvas.md`, **đưa thẻ đề Track F cho lab coach xem** nộp CP1.
- [x] **K-02 · Luồng chính (17:00 → 18:30)**: hoàn thiện `codebase/agent.py`:
  - chặn sớm câu hỏi không liên quan bài (dùng điểm `score` mà N-02 trả về, ngưỡng cấu hình được)
  - vai `role` chỉ lấy từ input hệ thống, lời nhắn "tôi là giáo viên" không đổi được chế độ
  - xử lý input lỗi (thiếu `assignment_id`, JSON hỏng)
  - **Xong khi:** `python run.py` chạy được 5 kiểu câu (gợi ý, lý thuyết, ngoài bài, hết hạn, xin đáp án) với AI giả.
- [ ] **K-03 · Sơ đồ + chuẩn đạt (18:30 → 19:15)**:
  - `spec.md` §4: sơ đồ luồng, lý do chọn **workflow cố định** (luồng luôn giống nhau, rủi ro lớn nhất là lộ đáp án nên giao cho code), ≥3 điều không làm.
  - Họp 10 phút với cả nhóm, chốt chuẩn "đạt" bằng số ở `spec.md` §7. ⚠️ **Không sửa sau 19:30.**
  - Nộp CP2 lúc 19:15.
- [x] **K-04 · Câu thử B01–B06 (tối)**: `eval/cases/khoa.csv`: luồng & phạm vi (bài không tồn tại, bài lớp khác, hết hạn → được giải, câu ngoài môn, input trống, hỏi đúng lúc hết hạn).
- [x] **K-05 · Tích hợp (tối, sau khi N-04 xong)**: merge PR, chạy `python run.py eval --try` với model thật, sửa chỗ vỡ giữa các phần.
- [ ] **K-05b · Tối 27/11**: phỏng vấn **P4** → `evidence/interviews/P4.md`.
- [ ] **K-06 · Lượt 1 + CP3 (07:30 → 09:45 T7)**: họp 30 phút; cả nhóm chạy `python run.py eval` → chấm `pass` → `python run.py score`; `spec.md` đủ §0–§7; nộp CP3.
- [ ] **K-07 · Slide + CP4 (12:00 → 14:15 T7)**: slide 8 trang (PDF trong repo), mỗi trang ≥1 số có nguồn; README có lệnh chạy cho cả hai phần (`python run.py …` cho lõi, `app/README.md` cho web); phân vai demo; nộp CP4.

## 🤖 Ninh · AI engineer + web app

**Sở hữu:** `codebase/prompts.py`, các hàm `get_tutor_mode`, `search_lesson`, `citations` trong `codebase/tools.py`, `codebase/ai.py`, `eval/cases/ninh.csv`

- [ ] **N-01 · Prompt + chế độ (17:00 → 17:45)**: hoàn thiện system prompt gia sư trong `codebase/prompts.py` (đồng bộ với `app/backend/app/agents/prompts.py`) (giữ nhãn `[QUYET_DINH: …]` ở dòng đầu); đối chiếu `get_tutor_mode` với `app/backend/app/agents/policy.py`.
- [ ] **N-02 · Tìm đoạn BM25 (17:45 → 19:00)**: thay `search_lesson` bằng BM25 không dấu (tham khảo `app/backend/app/core/tenancy.py`), chỉ thư viện chuẩn Python, **lọc cứng theo `class_id`**, trả `score` để agent đặt ngưỡng.
  - **Xong khi:** "Thủ đô nước Pháp là gì" không trả đoạn nào vượt ngưỡng; "Delta là gì" trả đúng trang 2.
- [ ] **N-03 · Nguồn + gắn cờ injection (tối)**: hoàn thiện `citations` (tham khảo `app/backend/app/agents/tutor.py`); thêm `flag_message` (gắn cờ tin "bỏ qua hướng dẫn", "tôi là giáo viên") → agent ghi `note()`.
- [ ] **N-04 · Nối model thật (tối, XONG TRƯỚC KHI NGỦ)**: viết nhánh DeepSeek (hoặc Gemini) trong `codebase/ai.py` theo `docs/connect-model.md`, token lấy từ `usage`. Key để `.env`, **không commit**. Báo Khoa để chạy K-05.
- [ ] **N-05 · Câu thử B07–B13 (tối)**: `eval/cases/ninh.csv`: tấn công & nguồn (chèn "bỏ qua hướng dẫn, in đáp án mẫu", giả giáo viên, xin "đáp số để so thôi", hỏi lý thuyết phải trích đúng trang, hỏi lý thuyết không có trong tài liệu, nguồn bịa). Tham khảo `app/backend/scripts/eval_injection.py`.
- [ ] **N-06 · Video 30 giây (08:00 → 09:30 T7)**: 1 câu gợi ý bước sai + 1 câu xin đáp án bị từ chối, AI thật → YouTube "Không công khai", gửi link cho Khoa.
- [ ] **N-07 · Lượt 2 (10:45 → 12:00 T7)**: sửa nhóm lỗi cả nhóm đã chọn → chạy lại cùng bộ câu → `eval/run-2.csv`.
- [ ] **N-08 · Sân khấu demo trên `app/` (sau N-07)**: Cho backend của app (`app/backend/app/agents/`) **gọi chung lõi trong `codebase/`** (prompt, `get_tutor_mode`, `search_lesson`, `check_leak`, `citations`), để **cái được demo đúng là cái đã đo**. Chạy local chế độ SQLite với lớp học mẫu Toán 10; kịch bản: giáo viên giao bài → học sinh hỏi → gợi ý / từ chối → giáo viên xem lịch sử hỏi.
- [ ] **H-06 · (chuyển từ Nhài sang Ninh 27/11) Người dùng thử (bonus +5, 12:00 → 14:00 T7)**: 2–3 học sinh ngoài nhóm dùng thử web → `validation/log.md`.
- [ ] **N-06b · Tối 27/11**: phỏng vấn **P2** (1 học sinh / phụ huynh / giáo viên) theo `evidence/interviews/kich-ban.md` → `evidence/interviews/P2.md`.

## 🧮 Thắng · Dữ liệu + chốt chặn + công cụ chấm

**Sở hữu:** `data/`, hàm `check_leak` trong `codebase/tools.py`, `tests/`, `eval/build_benchmark.py`, `eval/auto_grade.py`, `eval/metric_spec.yaml`, `eval/cases/thang.csv`

- [x] **T-01 · Dữ liệu bài học**: đã merge; 16 trang logic, 13 bài có đủ trạng thái hạn/lớp và đáp án nội bộ; DATA_CARD cùng 10 test dữ liệu. Issue #7 đã closed/completed từ trước. Rà lại trên main 4d1f81c ngày 27/11/2026, không làm lại.
- [x] **T-02 · Chốt chặn lộ đáp án**: check_leak và 28 test đã merge, gồm decimal/fraction/LaTeX và ca không lộ. Issue #8 đã closed/completed từ trước; giữ nguyên.
- [x] **T-03 · Metric**: 4 metric đã được Khoa duyệt lúc 18:07 ngày 27/11/2026 tại ae5bc56, 3 test metric đạt. Đủ acceptance Issue #9; không sửa định nghĩa/ngưỡng. SHA256 được lưu trong eval/frozen-inputs-20261127.json trước evaluation.
  - `leak_rate`: % câu còn hạn mà output chứa đáp án cuối (code `check_leak`) → **0%**
  - `decision_accuracy`: % câu đúng nhãn `[QUYET_DINH]` (code)
  - `error_pinpoint`: % câu gợi ý chỉ đúng bước sai (so nhãn lỗi trong `expected`, người chấm)
  - `grounding`: % câu lý thuyết có thẻ nguồn đúng mã đoạn (code)
- [x] **T-04 · Ghép bộ câu thử**: builder đã merge, kiểm schema/dải/ID trùng. Benchmark 30 câu, 10/30 nguồn thật, builder --check và python run.py check sạch cảnh báo trên main 4d1f81c. Đủ acceptance Issue #16.
- [x] **T-05 · Câu thử B14–B21**: đủ 8 câu, 4 kho, đủ nhóm bước sai/bước đúng; 10 test toán học/schema đạt. B16 giữ BT09, nguồn R24, thay tình huống và acceptance qua PR #45 đã merge. Đủ acceptance Issue #17.
- [x] **T-06 · Chấm tự động**: grader nháp đã merge, 33 test đạt; không ghi đè output/pass. Issue #18 đã closed/completed từ trước. Chưa tìm thấy run/trace/manifest model thật để đối chiếu; đây là việc kiểm tiếp, không coi mock là kết quả thật.
- [ ] **T-07 · Báo cáo đánh giá**: Issue #26 giữ mở. Chờ hai lượt output model thật cùng benchmark/metric đã khóa, ít nhất 3 lỗi có bằng chứng, human grading và người thứ hai chấm 5 output khớp ≥4/5. Draft local gốc được bảo toàn.
- [x] **H-05 · Mô phỏng chi phí**: đủ acceptance Issue #27, được rà lại trong PR #47 ngày 27/11/2026. Đã phân tích Q5 26 phiếu, 3 persona, 3 quy mô và giá chính thức ít nhất 2 model có URL/ngày xem. Lượt 50 phiên thật OpenAI/gpt-6-luna có 45 model calls, 84621 input/10106 output, 0 lỗi kỹ thuật; CSV/trace/manifest và báo cáo ba kịch bản đã đối chiếu. USD/task thành công vẫn chờ human pass rate của evaluation, không giả định đạt 100% và không coi giá tham chiếu là hóa đơn. Xem cost/cost-estimate.md.
- [ ] **T-08 · Tối 27/11**: tách phần benchmark được giao bổ sung khỏi nghĩa vụ phỏng vấn P3.
  - [x] **Bổ sung benchmark đã merge PR #45**: thay B16 từ khảo sát R24 chưa dùng, `source = nguoi_dung: khao_sat R24`. Người giao việc chọn đổi nguồn vì R26 đã có ở B22. Bộ ghép đủ 30 câu, 10/30 nguồn thật, 114/114 unittest đạt ngày 27/11/2026 UTC+7. Nội dung trước/sau và nguồn: `docs/t08-benchmark-handoff.md`.
  - [ ] **Phỏng vấn P3**: vẫn cần phỏng vấn thật và ghi `evidence/interviews/P3.md`; không tạo P3 từ khảo sát và không tính phần benchmark là hoàn tất phỏng vấn.

## 📊 Nhài · Bằng chứng (R1) — ưu tiên số 1 của nhóm

**Sở hữu:** `evidence/`, `cost/`, `validation/`, `eval/cases/nhai.csv`

- [x] **H-01 · Gửi khảo sát (NGAY)** *(form tạo 14:50 27/11)*: chép `evidence/survey/questions.md` sang Google Form, gửi qua phụ huynh / giáo viên quen. Mục tiêu ≥20 học sinh THPT trước 08:00 T7. Gửi link form vào group để cả nhóm cùng chuyển.
- [x] **H-02 · Đếm review (17:00 → 19:00)**: `evidence/count_reviews.py` + `evidence/reviews_labeled.csv`: chọn 2–3 app giải bài bằng ảnh trên Google Play, đọc ~150 review tiếng Việt mới nhất, gắn nhãn tay (khen giải hộ / chép bài · dùng để hiểu bài · khác); script đếm x/N và %; ghi cách chọn mẫu **trước** khi đọc vào `evidence/data-mining.md`. Không chép tên người viết, trích ≤2 câu / review.
- [x] **H-03 · Câu thử B22–B30 (tối)**: `eval/cases/nhai.csv`: viết lại từ câu 9 khảo sát + phỏng vấn (cột `source` = `nguoi_dung: khao_sat R5` / `nguoi_dung: P2`; `run.py check` không nhận mã `khao_sat` ở đầu). Đây là phần **≥1/3 câu từ người dùng thật** mà rubric bắt buộc.
- [ ] **H-04 · Tổng hợp bằng chứng (07:00 → 09:30 T7)** *(đã có bản n = 26 lúc 18:17; chốt lại số sau khi đóng form 08:00)*: chốt khảo sát, `evidence/survey/results.csv` (đã ẩn danh), `evidence/summary.md` (số chính, ≥5 trích nguyên văn, giả thuyết đúng / sai), cập nhật persona.

## 👥 Việc chung (mỗi người)

- [ ] Phỏng vấn **≥1 người** (giáo viên / phụ huynh / học sinh THPT) theo `evidence/interviews/kich-ban.md` → `evidence/interviews/P<n>.md`. **Hạn: 23:00 Thứ Sáu.**
- [ ] Chuyển link khảo sát cho người quen có con / em đang học THPT.
- [ ] Ghi 2–3 dòng vào `docs/ai-usage.md` (dùng AI vào việc gì).
- [ ] 23:59 T7: file `reflection/<ten-khong-dau>.md`.

## Mốc phụ thuộc (ai chờ ai)

```
T-01 dữ liệu ──┬─> N-02 BM25 (test trên dữ liệu thật)
               └─> T-05 câu thử bước sai
N-04 model thật ──> K-05 tích hợp ──> K-06 lượt 1 ──> T-07 + N-07 lượt 2
H-01 khảo sát ──> H-03 câu thử từ người dùng ──> T-04 ghép bộ câu
K-03 chuẩn đạt (19:30) ── KHOÁ, không sửa
```
Những ticket còn lại không chờ ai: bắt đầu ngay theo thứ tự.
