"""Đếm nhãn review app giải bài — H-02. Cách đếm ghi trước ở evidence/data-mining.md mục 1.

Chạy: python evidence/count_reviews.py            (đọc evidence/reviews_labeled.csv)
Cột của CSV: id, app, ngay, so_sao, trich, nhan, ghi_chu
  - trich: ≤2 câu, KHÔNG chép tên người viết
  - nhan: giai_ho  (khen giải hộ / chép bài / nộp nhanh)
          hieu_bai (dùng để hiểu bài, xem cách làm từng bước, kiểm tra lại bài đã làm)
          khac     (lỗi app, quảng cáo, giá tiền, khen chung chung…)
Người khác chạy lại phải ra cùng số.
"""
import csv
import os
import sys
from collections import Counter, defaultdict

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reviews_labeled.csv")
LABELS = ["giai_ho", "hieu_bai", "khac"]


def pct(x, n):
    return "%d/%d (%.0f%%)" % (x, n, 100.0 * x / n) if n else "0/0"


def main(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("id") or "").strip()]
    if not rows:
        sys.exit("Chưa có review nào trong %s" % path)
    bad = [r["id"] for r in rows if (r.get("nhan") or "").strip() not in LABELS]
    if bad:
        sys.exit("Nhãn sai / thiếu ở: %s (chỉ dùng %s)" % (", ".join(bad), ", ".join(LABELS)))

    n = len(rows)
    total = Counter(r["nhan"].strip() for r in rows)
    by_app = defaultdict(Counter)
    for r in rows:
        by_app[r["app"].strip()][r["nhan"].strip()] += 1

    print("Mẫu số: %d review đã đọc và gắn nhãn\n" % n)
    print("| Đếm gì | x / N | Ghi chú |\n|---|---|---|")
    for lb in LABELS:
        print("| nhãn %s | %s | tất cả app |" % (lb, pct(total[lb], n)))
    on_topic = total["giai_ho"] + total["hieu_bai"]
    print("| giai_ho trong số review nói về cách dùng (bỏ 'khac') | %s | mẫu số = giai_ho + hieu_bai |"
          % pct(total["giai_ho"], on_topic))
    print("\nTheo app:\n\n| App | N | giai_ho | hieu_bai | khac |\n|---|---|---|---|---|")
    for app, c in sorted(by_app.items()):
        m = sum(c.values())
        print("| %s | %d | %s | %s | %s |" % (app, m, pct(c["giai_ho"], m), pct(c["hieu_bai"], m), pct(c["khac"], m)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else PATH)
