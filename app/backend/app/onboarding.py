"""Onboarding: tạo sẵn Lớp học mẫu cho giáo viên mới để thử AI ngay trong 30 giây đầu."""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core import storage
from app.ingestion.pipeline import extract_pages, save_pages_and_chunks
from app.models import AIMode, Assignment, AssignmentVersion, Classroom, DocStatus, Document
from app.routers.common import utcnow

DEMO_FILE = "Bai_giang_mau_Dao_ham.md"

DEMO_LECTURE = """# Chương V. Đạo hàm (bài giảng mẫu)
Bài giảng mẫu do MinutesStudy tạo sẵn để thầy cô thử trợ lý AI. Nội dung: định nghĩa đạo hàm, ý nghĩa hình học,
quy tắc tính đạo hàm, đạo hàm của hàm hợp, đạo hàm của hàm số lượng giác.
---page---
## 1. Định nghĩa đạo hàm tại một điểm
Cho hàm số y = f(x) xác định trên khoảng (a; b) và x0 thuộc (a; b). Nếu tồn tại giới hạn hữu hạn
lim (x→x0) [f(x) − f(x0)] / (x − x0)
thì giới hạn đó được gọi là đạo hàm của hàm số y = f(x) tại điểm x0, kí hiệu f'(x0).
Đặt Δx = x − x0 (số gia của biến số) và Δy = f(x0 + Δx) − f(x0) (số gia của hàm số), ta có f'(x0) = lim (Δx→0) Δy/Δx.
---page---
## 2. Ý nghĩa hình học của đạo hàm
Đạo hàm f'(x0) là hệ số góc của tiếp tuyến với đồ thị hàm số y = f(x) tại điểm M(x0; f(x0)).
Phương trình tiếp tuyến tại M là: y = f'(x0)(x − x0) + f(x0).
Ý nghĩa vật lí: nếu s = s(t) là phương trình chuyển động thì vận tốc tức thời tại thời điểm t0 là v(t0) = s'(t0).
---page---
## 3. Đạo hàm của một số hàm số thường gặp
(c)' = 0 với c là hằng số; (x)' = 1.
(x^n)' = n·x^(n−1) với n là số tự nhiên lớn hơn 1.
(√x)' = 1 / (2√x) với x > 0.
(1/x)' = −1/x² với x ≠ 0.
---page---
## 4. Quy tắc tính đạo hàm
Cho u = u(x), v = v(x) có đạo hàm. Khi đó:
(u + v)' = u' + v'; (u − v)' = u' − v'
(u·v)' = u'·v + u·v'
(k·u)' = k·u' với k là hằng số
(u/v)' = (u'·v − u·v') / v² với v ≠ 0.
Ví dụ: y = x³ − 2x + 5 thì y' = 3x² − 2.
---page---
## 5. Đạo hàm của hàm hợp
Nếu hàm số u = g(x) có đạo hàm tại x là u'x và hàm số y = f(u) có đạo hàm tại u là y'u thì hàm hợp y = f(g(x))
có đạo hàm tại x là: y'x = y'u · u'x (quy tắc dây chuyền).
Hệ quả: (u^n)' = n·u^(n−1)·u' và (√u)' = u' / (2√u).
Ví dụ: y = (x² + 1)³. Đặt u = x² + 1 thì u' = 2x, nên y' = 3(x² + 1)²·2x = 6x(x² + 1)².
---page---
## 6. Đạo hàm của hàm số lượng giác
(sin x)' = cos x; (cos x)' = −sin x; (tan x)' = 1/cos²x; (cot x)' = −1/sin²x.
Với hàm hợp u = u(x): (sin u)' = u'·cos u; (cos u)' = −u'·sin u; (tan u)' = u'/cos²u.
Ví dụ: y = sin(2x) thì y' = 2cos(2x).
---page---
## 7. Bài tập tự luyện
1) Tính đạo hàm y = (3x − 1)^4.
2) Tính đạo hàm y = cos(5x).
3) Tính đạo hàm y = √(1 + x²).
4) Viết phương trình tiếp tuyến của đồ thị y = x² tại điểm có hoành độ x0 = 1.
"""

DEMO_PROMPT = """Câu 1: Tính đạo hàm của hàm số y = (2x² − 3x + 1)^5.
Câu 2: Tính đạo hàm của hàm số y = sin(3x² + 1).
Câu 3: Cho f(x) = √(x² + 4). Tính f'(0) và f'(2)."""

DEMO_RUBRIC = """Câu 1 — áp dụng đúng (u^n)' = n·u^(n−1)·u': 3 điểm
Câu 2 — áp dụng đúng (sin u)' = u'·cos u: 3 điểm
Câu 3 — tính đúng f'(x) và hai giá trị: 4 điểm"""

DEMO_ANSWER = """Câu 1: y' = 5(2x² − 3x + 1)^4·(4x − 3).
Câu 2: y' = 6x·cos(3x² + 1).
Câu 3: f'(x) = x/√(x² + 4); f'(0) = 0; f'(2) = 2/√8 = √2/2."""


def create_demo_class(db: Session, teacher_id: str) -> Classroom:
    from app.routers.teacher import class_code

    c = Classroom(teacher_id=teacher_id, name="Lớp học mẫu - Toán 11", subject_id="Toán",
                  ai_mode=AIMode.STRICT.value, class_code=class_code(db, "Lop mau"))
    db.add(c)
    db.flush()
    data = DEMO_LECTURE.encode("utf-8")
    d = Document(class_id=c.id, file_name=DEMO_FILE, file_key="", content_type="text/markdown", is_demo=True)
    db.add(d)
    db.flush()
    d.file_key = storage.put_file(f"classes/{c.id}/documents/{d.id}.md", data, "text/markdown")
    pages = extract_pages(data, DEMO_FILE)
    save_pages_and_chunks(db, d, c, pages)
    d.status, d.page_count = DocStatus.READY.value, len(pages)
    a = Assignment(class_id=c.id, due_at=utcnow() + timedelta(days=7), allow_late=True, current_version=1)
    db.add(a)
    db.flush()
    db.add(AssignmentVersion(assignment_id=a.id, version=1, title="Bài tập mẫu — Đạo hàm hàm hợp",
                             prompt=DEMO_PROMPT, rubric=DEMO_RUBRIC, reference_answer=DEMO_ANSWER))
    return c
