# Neronmen — MinutesStudy Tutor: gia sư không lộ đáp án

**Track F · Giáo dục phổ thông.** Học sinh THPT bí bài tập Toán về nhà thường chụp app giải bài rồi chép nguyên lời giải. MinutesStudy Tutor, khi bài **còn hạn nộp**, chỉ ra **bước sai đầu tiên** và gợi ý bước tiếp — **không đưa đáp án**; chỉ dùng tài liệu giáo viên đã đăng, có trích trang. Hết hạn mới được giải đầy đủ.

**Thành viên, lớp, track:** [TEAMS.md](TEAMS.md) · Canvas + thẻ đề Track F: [canvas.md](canvas.md) · Thiết kế, chuẩn "đạt": [spec.md](spec.md) · Việc từng người: [TICKETS.md](TICKETS.md)

**Lát cắt:** một học sinh THPT · hỏi về một bài tập Toán còn hạn, kèm bước làm · AI quyết định *gợi ý bước sai* / *trả lời lý thuyết kèm trang* / *nói "không có trong bài"* / *từ chối xin đáp án* · học sinh tự làm ra bài.

## Chạy nhanh (lõi gia sư — phần được chấm)

```bash
python run.py                      # gõ câu hỏi, chạy với AI giả nếu chưa có .env
cp .env.example .env               # Windows: copy .env.example .env — rồi điền:
#   MODEL_PROVIDER=deepseek   MODEL_NAME=deepseek-chat   API_KEY=<key của bạn>
python run.py eval --try           # 3 câu đầu với model thật
python run.py eval                 # cả bộ eval/benchmark.csv → eval/run-N.csv
python run.py check                # kiểm bộ câu thử, metric, TEAMS.md
```
Không cần `pip install` cho lõi (chỉ thư viện chuẩn Python 3.10+). Test: `pip install pytest && python -m pytest tests`.

Ô `input` của câu thử là JSON do **hệ thống** điền (vai, lớp, bài, giờ hỏi), chỉ `message` là học sinh gõ:
```json
{"role": "student", "class_id": "10A1", "assignment_id": "BT01", "asked_at": "2026-11-28T21:00:00+07:00", "message": "Em tính Delta = 25 + 24 = 49 rồi bí"}
```

## Web demo
- Bản đang chạy: **https://k5-day15-l3-b-neronmen.vercel.app** (Vercel → API Render → Supabase). Gói free của Render ngủ sau 15 phút: lần mở đầu chờ ~30–50 giây.
- Khung "Trợ lý giải bài" trên web gọi **chung lõi `codebase/`** đã đo bằng eval (`app/backend/app/agents/core_bridge.py`; image Render `app/backend/Dockerfile.render` mang theo `codebase/` + `data/`).
- **Kịch bản demo 3 phút + hướng dẫn dùng web + dữ liệu demo:** [demo/KICH_BAN_DEMO.md](demo/KICH_BAN_DEMO.md). Nạp lớp demo: `python demo/seed_demo.py --api <địa chỉ API>`.
- Chạy trên máy và cách deploy: [app/README.md](app/README.md), [app/docs/deploy-vercel-supabase-render.md](app/docs/deploy-vercel-supabase-render.md).

## Cấu trúc

| Thư mục | Là gì |
|---|---|
| `codebase/` | Lõi gia sư: `agent.py` (luồng), `tools.py` (7 công cụ), `prompts.py`, `ai.py` (nối model) |
| `data/` | Bài giảng Toán 10 (16 trang) + 13 bài tập — **tự dựng**, xem `data/DATA_CARD.md` |
| `eval/` | Bộ câu thử, metric, `build_benchmark.py`, `auto_grade.py`, các lượt chạy |
| `evidence/` | Khảo sát, phỏng vấn, đếm review — bằng chứng pain |
| `cost/` | Persona + mô phỏng chi phí |
| `app/` | Web MinutesStudy (FastAPI + Next.js) dùng làm demo |
| `tests/` | Test cho dữ liệu, `check_leak`, metric, bộ chấm |

## Phần nào thật, phần nào giả

| Thành phần | Thật / Giả | Ghi chú |
|---|---|---|
| Lời gọi AI ở quyết định trung tâm | **Thật** | DeepSeek `deepseek-chat` (đổi được sang Gemini / OpenAI trong `.env`) |
| Chế độ gợi ý / giải, chặn lộ đáp án, lọc nguồn, lọc lớp | **Thật** — chạy bằng code | `get_tutor_mode`, `check_leak`, `citations`, kiểm lớp trong `agent.py` |
| Bài giảng, bài tập, bước làm sai của học sinh | **Giả** — nhóm tự dựng | `data/DATA_CARD.md`; không dùng bài làm thật của học sinh |
| Bằng chứng pain | **Thật** — đang thu | khảo sát học sinh THPT, phỏng vấn, đếm review công khai (`evidence/`) |

## Dùng AI vào việc gì
Nhóm dùng trợ lý AI lập trình để dựng khung, viết test và soát tài liệu; mỗi người tự kiểm và giải thích được phần có tên mình. Chi tiết: [docs/ai-usage.md](docs/ai-usage.md).

---

*Phần dưới là hướng dẫn chung của bộ khung BTC (giữ lại để tra lệnh).*

## Chạy trong 3 phút

Bộ khung cần **Python 3.10 trở lên** (Python 3.9 có sẵn trên macOS vẫn chạy được, chỉ in một dòng nhắc). **Không cần `pip install`.**

**Bước 1 — Mở cửa sổ lệnh ngay trong thư mục repo**

| Windows (PowerShell) | macOS |
|---|---|
| Mở thư mục repo bằng File Explorer → bấm vào thanh địa chỉ → gõ `powershell` → Enter | Mở **Terminal** (Cmd + Space, gõ "Terminal") → gõ `cd ` (có dấu cách) → kéo thả thư mục repo vào → Enter |

Gõ `dir` (Windows) hoặc `ls` (macOS / Linux): thấy `run.py` và `README.md` là đang đứng đúng chỗ.

**Bước 2 — Kiểm Python và chạy thử**

| Việc | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Kiểm Python | `python --version` (không được thì `py --version`) | `python3 --version` |
| Chạy bản chạy thử (chế độ giả, chưa gọi model) | `python run.py` | `python3 run.py` |
| Kiểm bộ câu thử | `python run.py check` | `python3 run.py check` |
| Tạo file `.env` để nối model | `copy .env.example .env` | `cp .env.example .env` |

- Windows: gõ `python` mà mở Microsoft Store hoặc báo không có lệnh → dùng `py`. Chưa có Python: cài từ python.org, **tick "Add python.exe to PATH"**, mở lại PowerShell.
- macOS: báo `command not found: python` là bình thường → dùng `python3`.
- `python run.py` in ra "[câu trả lời giả — chưa nối model] …" là khung chạy đúng. Nối model thật: [docs/connect-model.md](docs/connect-model.md).

Trong README này lệnh viết là `python …`; máy nhóm cần `python3` hay `py` thì gõ thay.

## Lệnh

| Lệnh | Làm gì |
|---|---|
| `python run.py` | Chạy bản chạy thử (gõ đầu vào, nhận kết quả, kèm số lần gọi model / token) |
| `python run.py check` | Kiểm `eval/benchmark.csv` (6 cột, số câu, `kho` / `tu_choi`, mã `source`, ô trống, dòng mẫu) `eval/metric_spec.yaml` (≥3 metric điền đủ) và `TEAMS.md` (đúng format để BTC quét). Chỉ cảnh báo, không sửa file |
| `python run.py eval --try` | **Thử nối model:** chạy 3 câu đầu (`--try 5` = 5 câu) → `eval/run-try.csv`. Thấy "Nối model được" là xong. Không tính là một lượt |
| `python run.py eval` | Chạy cả bộ qua `codebase/agent.py` → `eval/run-1.csv` (lần sau `run-2.csv`…) + `traces/run-1.jsonl`. Mỗi dòng có run ID, model, số lần gọi model / công cụ, token. Model còn giả → chỉ ghi `run-mock.csv`; mọi câu lỗi → `run-error.csv`; Ctrl+C → `run-stopped.csv` — đều **không** được đánh số |
| `python run.py eval --fake` | Thử riêng bộ chạy, không gọi agent → `eval/run-fake.csv` |
| `python run.py score eval/run-1.csv` | Sau khi điền cột `pass` (1 / 0): in % đạt tổng và theo `type`. Còn ô trống → "CHƯA CHẤM XONG", không in % |
| `python run.py simulate --try` | Thử mô phỏng chi phí 10 phiên (làm trước CP3) → `cost/simulate-try.csv` |
| `python run.py simulate` | Mô phỏng chi phí khi dùng thật theo `cost/personas.yaml` (≥50 phiên) → `cost/simulate-N.csv` + `cost/simulate-N-summary.md` |
| `python run.py simulate --rate-from eval/run-2.csv` | Như trên, lấy tỉ lệ đạt từ đúng lượt chỉ định. Không ghi thì khung lấy lượt `run-N` mới nhất đã chấm, cùng model, và ghi rõ đã lấy lượt nào trong bản tóm tắt |

Gói miễn phí báo hết lượt: thêm `--wait 4` sau `eval` hoặc `simulate` (nghỉ 4 giây giữa hai lượt gọi). Sửa CSV bằng Excel: *File → Save As → CSV UTF-8*; Google Sheets: *Tệp → Tải xuống → CSV*.

**Lượt có lỗi kỹ thuật** (cột `error` có chữ): không sửa tay file đó, chạy lại thành lượt mới và ghi vào bảng các lượt ở `eval/README.md`. Không xoá file lượt nào.

Nhóm dùng stack khác (Node, Streamlit, notebook…): sửa hàm `run_app()` trong `run.py` để `python run.py` vẫn chạy được bản chạy thử, và giữ `answer()` trong `codebase/agent.py` để `eval`, `simulate` chạy được.

## Bản chạy thử — viết ở đâu

| File | Viết gì | Bước guide |
|---|---|---|
| `codebase/agent.py` | `answer(text)` — luồng chính, đúng hình dạng ở `spec.md` §4. Khung có sẵn một workflow 2 bước *ví dụ* | 3.2 |
| `codebase/tools.py` | Công cụ của bài toán, mỗi công cụ một hàm có `@tool` | 2.2, 3.2 |
| `codebase/ai.py` | `call_model(system, user)` — chỗ duy nhất gọi model. Chưa điền `.env` thì chạy **chế độ giả** | 3.3 |

- **Trước CP2:** để chế độ giả, công cụ trả dữ liệu giả — `python run.py` đi hết luồng là đủ.
- **Trước CP3:** nối model thật theo [docs/connect-model.md](docs/connect-model.md), `eval --try` thấy token > 0 rồi mới `eval`.
- Bộ chạy gửi **nguyên ô `input`** của câu thử vào `answer(text)`. Dữ liệu nền (bài học, thông báo, lịch…) để trong `data/`, đọc qua công cụ.

## File mẫu — điền ở bước nào

| File | Điền ở bước guide | Mốc |
|---|---|---|
| `TEAMS.md` | 1.0 | CP1 · **đúng format**, BTC quét khi chấm |
| `canvas.md` | 1.4 | CP1, cập nhật CP2 |
| `evidence/hypothesis.md` | 1.1 | trước khi tìm bằng chứng |
| `evidence/data-mining.md` · `evidence/interviews/TEMPLATE.md` → `P1.md`… · `evidence/survey/TEMPLATE.md` | 1.2 | bắt đầu sau Zoom, xong CP3 |
| `evidence/summary.md` | 1.2 | CP3 |
| `spec.md` | §0–§2: 1.1–1.3 · §3–§5: 2.1–2.3 · §7: 2.4 · §8: 4.2 · §10: suốt | §7 chốt CP2 · §0–§7 CP3 · đủ CP4 |
| `data/DATA_CARD.md` | 2.4 | bản đầu CP2 |
| `eval/benchmark.csv` · `eval/metric_spec.yaml` | 2.4 | ≥10 câu + metric chốt CP2 · 20–30 câu CP3 |
| `codebase/` | 3.2, 3.3 | khung CP2 · AI thật CP3 |
| `eval/report.md` · `eval/README.md` | 4.1 (README mục 1–4 từ 2.4) | CP4 |
| `cost/personas.yaml` · `cost/cost-estimate.md` | 4.2 | thử 10 phiên CP3 · đủ CP4 |
| `validation/log.md` *(bonus)* | 4.3 | CP4 |
| `slides/outline.md` → `demo-slides.pdf` | 5.1 | CP4 |
| `reflection/TEMPLATE.md` → `reflection/<ten>.md` | 5.3 | 23:59 Thứ Bảy 28/11 |
| `AGENTS.md` · `docs/ai-usage.md` | khi dùng coding agent / AI | suốt |

## Bảy hạng mục bắt buộc — nằm ở file nào

| # | Hạng mục | File |
|---|---|---|
| 1 | Bằng chứng pain | `evidence/` (tổng hợp ở `evidence/summary.md`) |
| 2 | Impact có số | `spec.md` §2 |
| 3 | Thiết kế giải pháp | `spec.md` §4 |
| 4 | Bản chạy thử làm trọn lát cắt | `codebase/` · lệnh ở mục "Lệnh" |
| 5 | Định nghĩa "tốt" + bộ câu thử | `data/DATA_CARD.md` · `eval/` |
| 6 | Mô phỏng chi phí khi dùng thật | `cost/` |
| 7 | Slide + demo + video dự phòng | slide trong repo (PDF, PPTX, HTML…) hoặc link slide ở form CP4 · link video: ____ |
| + | *Bonus:* người dùng thử | `validation/log.md` |
