"""Tạo PDF bài giảng demo từ data/lesson.json (lớp 10A1): mỗi trang của dữ liệu đo = đúng một trang PDF,
nên thẻ nguồn "Trang n" trên web khớp với bộ câu thử eval. Chữ giữ NGUYÊN VĂN data/lesson.json (không thêm kiến thức).

Chạy (cần fpdf2 và font Arial của Windows):  python demo/make_lesson_pdf.py
→ demo/Chuong3_Phuong_trinh_bac_hai.pdf
"""
import json
import sys
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo" / "Chuong3_Phuong_trinh_bac_hai.pdf"
FONT_DIR = Path("C:/Windows/Fonts")


class Lesson(FPDF):
    def header(self):
        self.set_font("body", "", 9)
        self.set_text_color(110, 110, 110)
        self.cell(0, 6, "Toán 10 · Chương 3 · Phương trình bậc hai — tài liệu giáo viên lớp 10A1", align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-14)
        self.set_font("body", "", 9)
        self.set_text_color(110, 110, 110)
        self.cell(0, 6, "Trang %d" % self.page_no(), align="C")


def main() -> int:
    pages = sorted((p for p in json.loads((ROOT / "data" / "lesson.json").read_text("utf-8")) if p["class_id"] == "10A1"),
                   key=lambda p: p["page"])
    if [p["page"] for p in pages] != list(range(1, len(pages) + 1)):
        print("Số trang lớp 10A1 không liên tục 1..n — dừng để thẻ nguồn không lệch trang")
        return 1
    pdf = Lesson(format="A4")
    pdf.set_margins(22, 18, 22)
    pdf.set_auto_page_break(False)
    pdf.add_font("body", "", str(FONT_DIR / "arial.ttf"))
    pdf.add_font("body", "B", str(FONT_DIR / "arialbd.ttf"))
    for p in pages:
        pdf.add_page()
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("body", "B", 17)
        pdf.multi_cell(0, 9, "%d. %s" % (p["page"], p["title"]))
        pdf.ln(4)
        pdf.set_font("body", "", 12.5)
        pdf.multi_cell(0, 7.2, p["text"])
    pdf.output(str(OUT))
    print("Đã tạo %s (%d trang)" % (OUT.relative_to(ROOT), len(pages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
