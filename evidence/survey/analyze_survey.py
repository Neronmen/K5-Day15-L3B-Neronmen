"""Đếm kết quả khảo sát theo đúng luật đọc đã ghi TRƯỚC ở evidence/survey/questions.md.

Cách dùng (chỉ thư viện chuẩn):
  1) Google Sheet kết quả → Tệp → Tải xuống → CSV → lưu thành evidence/survey/raw-YYYYMMDD.csv (KHÔNG commit)
  2) python evidence/survey/analyze_survey.py anonymize evidence/survey/raw-YYYYMMDD.csv
       → ghi evidence/survey/results.csv: bỏ cột dấu thời gian, thêm mã R1, R2… (được commit)
  3) python evidence/survey/analyze_survey.py           (mặc định đọc results.csv)
       → in bảng markdown để chép vào evidence/summary.md
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.csv")

# Từ khoá nhận cột (tiêu đề cột Google xuất ra = nguyên văn câu hỏi)
COLS = {
    "q1": "Em đang học lớp",
    "q2": "không tự làm được là khi nào",
    "q3": "Lần đó em đã làm gì",
    "q4": "dùng lời giải đó thế nào",
    "q5": "Trong 1 tuần qua",
    "q6": "kiểm tra cùng dạng",
    "q7": "Vì sao em dùng lời giải",
    "q8": "bước nào sai",
    "q9": "Kể ngắn",
}
Q3_OPTS = ["Chụp ảnh lên app giải bài", "Hỏi ChatGPT / chatbot", "Tìm lời giải trên mạng", "Hỏi bạn",
           "Hỏi bố mẹ, anh chị", "Hỏi thầy cô / gia sư", "Xem lại vở, sách", "Bỏ qua bài đó"]
Q4_OPTS = ["Chép gần như nguyên vào bài", "Đọc hiểu rồi tự viết lại", "Chỉ xem đáp số để so",
           "Xem gợi ý một bước rồi tự làm", "Không dùng"]
Q5_OPTS = ["0", "1–2", "3–5", "6–10", "Trên 10"]
Q5_MID = {"0": 0, "1–2": 1.5, "3–5": 4, "6–10": 8, "Trên 10": 12}  # điểm giữa khoảng (Trên 10 → 12: tự ước tính)
Q6_OPTS = ["Làm được hết", "Làm được một phần", "Không làm được", "Chưa có bài kiểm tra như vậy"]
Q7_OPTS = ["Không biết bắt đầu từ đâu", "Làm sai mà không biết sai ở đâu", "Quá nhiều bài, không đủ thời gian",
           "Không có ai để hỏi lúc đó", "Chỉ cần nộp cho đủ"]
Q8_OPTS = ["Có", "Tuỳ bài", "Không, em muốn có đáp án luôn"]
DROP = ("dấu thời gian", "timestamp", "email", "địa chỉ email")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def anonymize(src):
    rows = read(src)
    if not rows:
        sys.exit("File trống: %s" % src)
    keep = [c for c in rows[0].keys() if not any(d in c.lower() for d in DROP)]
    with open(RESULTS, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ma"] + keep)
        for i, r in enumerate(rows, 1):
            w.writerow(["R%d" % i] + [r[c] for c in keep])
    print("Đã ghi %s (%d dòng, bỏ cột: %s)" % (RESULTS, len(rows),
          ", ".join(c for c in rows[0] if c not in keep) or "không có"))


def col(rows, key):
    for c in rows[0].keys():
        if COLS[key].lower() in c.lower():
            return c
    sys.exit("Không thấy cột chứa '%s' trong CSV" % COLS[key])


def frac(x, n):
    if n == 0:
        return "0/0"
    return "%d/%d" % (x, n) if n < 10 else "%d/%d (%.0f%%)" % (x, n, 100.0 * x / n)


def has(cell, opt):
    return opt in (cell or "")


def table(title, rows, c, opts, multi=False):
    n = len(rows)
    print("\n**%s** (mẫu số %d%s)\n" % (title, n, ", chọn nhiều nên tổng > 100%" if multi else ""))
    print("| Lựa chọn | x/N |\n|---|---|")
    for o in opts:
        x = sum(1 for r in rows if (has(r[c], o) if multi else (r[c] or "").strip() == o))
        print("| %s | %s |" % (o, frac(x, n)))
    if multi:
        other = [r[c] for r in rows if r[c] and not any(has(r[c], o) for o in opts)]
        if other:
            print("| Khác (tự ghi) | %s |" % frac(len(other), n))


def main(path):
    rows = read(path)
    if not rows:
        sys.exit("Chưa có câu trả lời nào trong %s" % path)
    c = {k: col(rows, k) for k in COLS}
    total = len(rows)
    hs = [r for r in rows if (r[c["q1"]] or "").strip() in ("10", "11", "12")]
    n = len(hs)
    print("# Kết quả khảo sát: %s\n" % os.path.basename(path))
    print("- Tổng phiếu: %d · **mẫu số chính (học sinh lớp 10–12): %d**%s"
          % (total, n, "" if n >= 20 else "  ⚠️ chưa đủ ngưỡng ≥20"))

    copy = [r for r in hs if (r[c["q4"]] or "").strip() == Q4_OPTS[0]]
    fail = [r for r in copy if (r[c["q6"]] or "").strip() in (Q6_OPTS[1], Q6_OPTS[2])]
    copy_tested = [r for r in copy if (r[c["q6"]] or "").strip() != Q6_OPTS[3]]
    p1 = len(copy) / n if n else 0
    p2 = len(fail) / len(copy) if copy else 0
    print("\n## Kiểm giả thuyết (luật ở questions.md)\n")
    print("| Điều kiện | Kết quả | Ngưỡng | Đạt? |\n|---|---|---|---|")
    print("| Câu 4 = Chép gần như nguyên | %s | ≥50%% | %s |" % (frac(len(copy), n), "✅" if p1 >= 0.5 else "❌"))
    print("| Trong số người chép: câu 6 = Một phần / Không làm được | %s | ≥40%% | %s |"
          % (frac(len(fail), len(copy)), "✅" if p2 >= 0.4 else "❌"))
    print("| (tham khảo) như trên nhưng bỏ người 'Chưa có bài kiểm tra' | %s | — | — |"
          % frac(len(fail), len(copy_tested)))

    table("Câu 2 — lần gần nhất không tự làm được", hs, c["q2"], ["Hôm nay / hôm qua", "Trong tuần này", "Tuần trước", "Lâu hơn", "Chưa bao giờ"])
    table("Câu 3 — lần đó đã làm gì", hs, c["q3"], Q3_OPTS, multi=True)
    table("Câu 4 — dùng lời giải thế nào", hs, c["q4"], Q4_OPTS)
    table("Câu 5 — số lần dùng app / chatbot trong 1 tuần", hs, c["q5"], Q5_OPTS)
    table("Câu 6 — kiểm tra cùng dạng", hs, c["q6"], Q6_OPTS)
    table("Câu 7 — vì sao dùng lời giải có sẵn", hs, c["q7"], Q7_OPTS, multi=True)
    reason_bad = sum(1 for r in hs if has(r[c["q7"]], Q7_OPTS[2]) or has(r[c["q7"]], Q7_OPTS[4]))
    print("\n→ Chọn 'Quá nhiều bài' hoặc 'Chỉ cần nộp cho đủ': %s (đa số → giả thuyết sai một phần)" % frac(reason_bad, n))
    table("Câu 8 — thái độ (chỉ tham khảo, KHÔNG phải bằng chứng pain)", hs, c["q8"], Q8_OPTS)

    # Persona chi phí: số lần / tuần
    vals = [Q5_MID[(r[c["q5"]] or "").strip()] for r in hs if (r[c["q5"]] or "").strip() in Q5_MID]
    if vals:
        print("\n## Cho cost/personas.yaml (câu 5)\n")
        print("- Trung bình ≈ %.1f lần / tuần (lấy điểm giữa khoảng; 'Trên 10' tính 12 — tự ước tính)" % (sum(vals) / len(vals)))
        for name, lo, hi in (("ít (0–2 lần/tuần)", 0, 2), ("vừa (3–5)", 3, 5), ("nhiều (≥6)", 6, 99)):
            x = sum(1 for v in vals if lo <= v <= hi)
            print("- %s: %s" % (name, frac(x, len(vals))))

    ma = "ma" if "ma" in rows[0] else None
    stories = [((r[ma] if ma else "R%d" % (i + 1)), r[c["q9"]].strip())
               for i, r in enumerate(rows) if r in hs and (r[c["q9"]] or "").strip()]
    print("\n## Câu 9 — kể nguyên văn (%d phiếu có kể) → trích vào summary.md, nguồn câu thử `nguoi_dung: khao_sat R_`\n" % len(stories))
    for m, s in stories:
        print("- **%s:** \"%s\"" % (m, s.replace("\n", " ")))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "anonymize":
        anonymize(sys.argv[2])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else RESULTS)
