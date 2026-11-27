"""Nạp lớp DEMO sạch lên web MinutesStudy qua API (chạy được với web thật trên Render hoặc backend trên máy).

Tạo (chạy lại thì dùng lại cái đã có, không tạo trùng):
  - 1 tài khoản giáo viên + 2 tài khoản học sinh (email bên dưới, mật khẩu DO BẠN NHẬP lúc chạy, không lưu ở đâu)
  - lớp "Toán 10A1 · Phương trình bậc hai", 2 học sinh đã vào lớp
  - tài liệu demo/Chuong3_Phuong_trinh_bac_hai.pdf (15 trang = đúng 15 trang data/lesson.json mà bộ câu thử dùng)
  - 4 bài tập lấy nguyên đề + đáp án mẫu từ data/assignments.json: 3 bài CÒN HẠN (chế độ gợi ý), 1 bài ĐÃ HẾT HẠN

Chạy (máy có Python, không cần cài thêm gì):
    python demo/seed_demo.py --api https://minutesstudy-api.onrender.com
    python demo/seed_demo.py --api http://localhost:8000
Mật khẩu: script hỏi khi chạy (ô nhập không hiện chữ), hoặc đặt biến môi trường DEMO_PASSWORD (≥ 8 ký tự).
Cả 3 tài khoản demo dùng chung mật khẩu đó. KHÔNG ghi mật khẩu vào repo.
"""
import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "demo" / "Chuong3_Phuong_trinh_bac_hai.pdf"
CLASS_NAME = "Toán 10A1 · Phương trình bậc hai"
TEACHER = {"email": "co.lan.demo@minutesstudy.app", "name": "Cô Lan", "role": "teacher"}
# 2 học sinh: Minh CHỈ dùng lúc demo thật (lịch sử chat sạch); An để tập dượt. Mỗi học sinh tối đa 60 câu hỏi AI / ngày.
STUDENTS = [{"email": "minh.demo@minutesstudy.app", "name": "Nguyễn Minh", "role": "student"},
            {"email": "an.taptrung@minutesstudy.app", "name": "Trần An (tập dượt)", "role": "student"}]
# (mã bài trong data/assignments.json, tên hiện trên web, còn hạn?). Đề + đáp án mẫu lấy nguyên từ data/.
ASSIGNMENTS = [("BT12", "Bài ôn tập tuần trước (đã hết hạn)", False),
               ("BT09", "Bài 3 · Nghiệm phân số và nghiệm âm", True),
               ("BT03", "Bài 2 · Công thức nghiệm khi a khác 1", True),
               ("BT01", "Bài 1 · Giải phương trình bậc hai", True)]
VN = timezone(timedelta(hours=7))


def call(api, path, token=None, body=None, method=None, files=None):
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if files:
        boundary = uuid.uuid4().hex
        name, content, ctype = files
        data = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                 % (boundary, name, ctype)).encode("utf-8") + content + ("\r\n--%s--\r\n" % boundary).encode())
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(api + path, data=data, headers=headers, method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except ValueError:
            return e.code, None


def account(api, info, password):
    """Đăng nhập; chưa có thì đăng ký. Trả token."""
    st, out = call(api, "/auth/login", body={"email": info["email"], "password": password})
    if st == 200:
        print("  · đăng nhập %s (%s)" % (info["name"], info["email"]))
        return out["access_token"]
    st, out = call(api, "/auth/register", body=dict(info, password=password))
    if st == 201:
        print("  · tạo tài khoản %s (%s)" % (info["name"], info["email"]))
        return out["access_token"]
    sys.exit("Không đăng nhập / đăng ký được %s: %s %s" % (info["email"], st, out))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", required=True, help="địa chỉ backend, vd https://minutesstudy-api.onrender.com")
    api = ap.parse_args().api.rstrip("/")
    if not PDF.is_file():
        sys.exit("Thiếu %s — chạy python demo/make_lesson_pdf.py trước" % PDF.relative_to(ROOT))
    password = os.environ.get("DEMO_PASSWORD") or getpass.getpass("Mật khẩu cho 3 tài khoản demo (≥ 8 ký tự): ")
    if len(password) < 8:
        sys.exit("Mật khẩu cần ≥ 8 ký tự")

    print("1) Tài khoản (web trên Render gói free có thể mất ~1 phút để thức dậy)…")
    t_tok = account(api, TEACHER, password)
    s_toks = [account(api, s, password) for s in STUDENTS]

    print("2) Lớp học…")
    st, classes = call(api, "/teacher/dashboard", t_tok)
    cls = next((c for c in classes or [] if c["name"] == CLASS_NAME), None)
    if cls is None:
        st, cls = call(api, "/teacher/classes", t_tok, {"name": CLASS_NAME, "subject": "Toán", "ai_mode": "strict"})
        if st != 201:
            sys.exit("Tạo lớp lỗi: %s %s" % (st, cls))
        print("  · tạo lớp, mã lớp %s" % cls["class_code"])
    else:
        print("  · đã có lớp, mã lớp %s" % cls["class_code"])
    for info, tok in zip(STUDENTS, s_toks):
        st, out = call(api, "/student/join", tok, {"class_code": cls["class_code"]})
        print("  · %s vào lớp: %s" % (info["name"], "ok" if st == 200 else "%s %s" % (st, out)))

    print("3) Tài liệu bài giảng…")
    st, docs = call(api, "/teacher/classes/%s/documents" % cls["id"], t_tok)
    doc = next((d for d in docs or [] if d["file_name"] == PDF.name and d["status"] != "failed"), None)
    if doc is None:
        st, doc = call(api, "/teacher/classes/%s/documents" % cls["id"], t_tok,
                       files=(PDF.name, PDF.read_bytes(), "application/pdf"))
        if st != 201:
            sys.exit("Upload tài liệu lỗi: %s %s" % (st, doc))
        print("  · đã upload %s, chờ AI đọc xong…" % PDF.name)
    for _ in range(60):
        if doc["status"] != "processing":
            break
        time.sleep(3)
        st, docs = call(api, "/teacher/classes/%s/documents" % cls["id"], t_tok)
        doc = next(d for d in docs if d["id"] == doc["id"])
    print("  · trạng thái tài liệu: %s, %s trang" % (doc["status"], doc.get("page_count")))
    if doc["status"] != "ready":
        sys.exit("Tài liệu chưa sẵn sàng (%s) — mở web tab Tài liệu bài giảng để xem lỗi" % doc.get("error"))

    print("4) Bài tập…")
    st, detail = call(api, "/teacher/classes/%s" % cls["id"], t_tok)
    have = {a["title"] for a in (detail or {}).get("assignments", [])}
    tasks = {a["id"]: a for a in json.loads((ROOT / "data" / "assignments.json").read_text("utf-8"))}
    now = datetime.now(VN)
    for code, title, open_ in ASSIGNMENTS:
        t = tasks[code]
        if title in have:
            print("  · đã có: %s" % title)
            continue
        # Còn hạn: 7 ngày nữa. Đã hết hạn: 2 ngày trước (để web mở chế độ lời giải).
        due = (now + timedelta(days=7) if open_ else now - timedelta(days=2)).replace(hour=23, minute=59, second=0, microsecond=0)
        st, out = call(api, "/teacher/classes/%s/assignments" % cls["id"], t_tok, {
            "title": title, "prompt": t["question"], "due_at": due.isoformat(),
            "reference_answer": t["answer_key"], "allow_late": True})
        print("  · %s: %s (hạn %s)" % ("tạo" if st == 201 else "LỖI %s" % st, title, due.strftime("%d/%m %H:%M")))

    print("\nXONG. Mã lớp: %s" % cls["class_code"])
    print("Giáo viên:              %s" % TEACHER["email"])
    print("Học sinh DEMO THẬT:     %s  (chỉ dùng lúc trình bày)" % STUDENTS[0]["email"])
    print("Học sinh TẬP DƯỢT:      %s" % STUDENTS[1]["email"])
    print("Mật khẩu cả 3: cái bạn vừa nhập")
    return 0


if __name__ == "__main__":
    sys.exit(main())
