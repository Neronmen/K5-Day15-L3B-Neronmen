"""Lấy review công khai trên Google Play (tiếng Việt, mới nhất) → evidence/reviews_labeled.csv — H-02.

Cách lấy mẫu ghi trước ở evidence/data-mining.md mục 1. Script:
  - lấy review mới nhất (sort NEWEST), lang=vi, country=vn
  - KHÔNG lưu tên người viết, ảnh đại diện, mã review
  - bỏ review chỉ có emoji hoặc ≤2 chữ; cắt mỗi review còn ≤2 câu
  - để trống cột `nhan` cho người gắn tay (giai_ho / hieu_bai / khac)

Chạy:
  pip install google-play-scraper
  python evidence/fetch_reviews.py            # mỗi app 50 review
  python evidence/fetch_reviews.py 60         # mỗi app 60 review
Sau đó gắn nhãn cột `nhan` rồi chạy: python evidence/count_reviews.py
"""
import csv
import os
import re
import sys

from google_play_scraper import Sort, reviews

APPS = [  # tên ngắn, mã app trên Google Play (khớp data-mining.md mục 1)
    ("Photomath", "com.microblink.photomath"),
    ("QANDA", "com.mathpresso.qanda"),
    ("AI Hay", "com.hay1.tintuc"),
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reviews_labeled.csv")
WORD = re.compile(r"[0-9A-Za-zÀ-ỹ]+")


def keep(text):
    """Bỏ review chỉ có emoji hoặc ≤2 chữ (luật lọc ở data-mining.md)."""
    return len(WORD.findall(text or "")) > 2


def two_sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+", " ".join(text.split()))
    return " ".join(parts[:2])


def main(per_app):
    rows, log = [], []
    for name, pid in APPS:
        got, token, seen = [], None, 0
        while len(got) < per_app:
            batch, token = reviews(pid, lang="vi", country="vn", sort=Sort.NEWEST,
                                   count=200, continuation_token=token)
            if not batch:
                break
            for r in batch:
                if len(got) >= per_app:
                    break
                seen += 1
                if keep(r["content"]):
                    got.append(r)
            if token is None or token.token is None:
                break
        log.append("%s: đọc %d review mới nhất, giữ %d sau khi lọc" % (name, seen, len(got)))
        for r in got:
            rows.append({"app": name, "ngay": r["at"].strftime("%d/%m/%Y"), "so_sao": r["score"],
                         "trich": two_sentences(r["content"]), "nhan": "", "ghi_chu": ""})

    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8-sig") as f:
            if sum(1 for _ in f) > 1:
                sys.exit("%s đã có dữ liệu — không ghi đè. Đổi tên file cũ trước nếu muốn lấy lại." % OUT)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "app", "ngay", "so_sao", "trich", "nhan", "ghi_chu"])
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow(dict(id=i, **r))
    print("\n".join(log))
    print("Đã ghi %d review → %s" % (len(rows), OUT))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 50)
