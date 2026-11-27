"""Giai đoạn 1: Auth, RBAC, quản lý lớp, bài tập, nộp bài."""
from datetime import datetime, timedelta, timezone

from tests.conftest import register

FUTURE = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
PAST = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def make_class(client, h, name="Toán 11A1 - Học kỳ 1"):
    r = client.post("/teacher/classes", json={"name": name, "subject": "Toán", "ai_mode": "strict"}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def make_assignment(client, h, class_id, due=FUTURE, allow_late=True):
    r = client.post(f"/teacher/classes/{class_id}/assignments", headers=h, json={
        "title": "Bài tập 3", "prompt": "Tính đạo hàm y = (2x² − 3x + 1)⁵", "due_at": due,
        "rubric": "Câu 1: 10đ", "reference_answer": "y' = 5(...)⁴(4x−3)", "allow_late": allow_late})
    assert r.status_code == 201, r.text
    return r.json()


# ---------- Auth ----------
def test_register_login_me(client):
    register(client, "co.trang@truong.edu.vn", "teacher", "Cô Trang")
    r = client.post("/auth/login", json={"email": "CO.TRANG@truong.edu.vn", "password": "matkhau123"})
    assert r.status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["role"] == "teacher"


def test_wrong_password_and_duplicate(client):
    register(client, "a@x.vn", "student")
    assert client.post("/auth/login", json={"email": "a@x.vn", "password": "sai-mat-khau"}).status_code == 401
    r = client.post("/auth/register", json={"email": "a@x.vn", "password": "matkhau123", "name": "A", "role": "student"})
    assert r.status_code == 409


def test_no_token_and_bad_token(client):
    assert client.get("/teacher/dashboard").status_code == 401
    assert client.get("/teacher/dashboard", headers={"Authorization": "Bearer abc"}).status_code == 401


# ---------- RBAC ----------
def test_student_cannot_use_teacher_api(client):
    hs = register(client, "hs@x.vn", "student")
    assert client.post("/teacher/classes", json={"name": "X", "subject": "Toán"}, headers=hs).status_code == 403


def test_only_owner_manages_class(client):
    t1 = register(client, "t1@x.vn", "teacher")
    t2 = register(client, "t2@x.vn", "teacher")
    c = make_class(client, t1)
    assert client.post(f"/teacher/classes/{c['id']}/students", json={"emails": ["a@x.vn"]}, headers=t2).status_code == 403
    assert client.get(f"/teacher/classes/{c['id']}", headers=t2).status_code == 403
    files = {"file": ("bai.pdf", b"%PDF-1.4 test", "application/pdf")}
    assert client.post(f"/teacher/classes/{c['id']}/documents", files=files, headers=t2).status_code == 403
    a = make_assignment(client, t1, c["id"])
    assert client.get(f"/teacher/assignments/{a['id']}/submissions", headers=t2).status_code == 403


# ---------- Lớp & học sinh ----------
def test_add_students_then_invited_student_activates(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    r = client.post(f"/teacher/classes/{c['id']}/students", headers=t,
                    json={"emails": ["giabao@hs.vn", "khong-hop-le", "GIABAO@hs.vn", "t@x.vn"]})
    body = r.json()
    assert body["added"] == ["giabao@hs.vn"]
    assert "khong-hop-le" in body["invalid"] and "t@x.vn" in body["invalid"]
    # Học sinh đăng ký bằng đúng email được mời → thấy lớp ngay
    hs = register(client, "giabao@hs.vn", "student", "Trần Gia Bảo")
    home = client.get("/student/home", headers=hs).json()
    assert [x["id"] for x in home["classes"]] == [c["id"]]


def test_import_csv(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    csv_data = "Họ tên,Email\nNguyễn Minh Anh,minhanh@hs.vn\nLê Phúc,phuc@hs.vn\n,\n".encode("utf-8-sig")
    r = client.post(f"/teacher/classes/{c['id']}/students/import", headers=t, files={"file": ("ds.csv", csv_data, "text/csv")})
    assert r.status_code == 200, r.text
    assert sorted(r.json()["added"]) == ["minhanh@hs.vn", "phuc@hs.vn"]
    names = {m["name"] for m in client.get(f"/teacher/classes/{c['id']}", headers=t).json()["members"]}
    assert "Nguyễn Minh Anh" in names


def test_join_by_code_and_dashboard(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    hs = register(client, "hs@x.vn", "student")
    assert client.post("/student/join", json={"class_code": "SAI-MA"}, headers=hs).status_code == 404
    assert client.post("/student/join", json={"class_code": c["class_code"].lower()}, headers=hs).status_code == 200
    dash = client.get("/teacher/dashboard", headers=t).json()
    assert dash[0]["students"] == 1


def test_upload_document_validation(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    bad = client.post(f"/teacher/classes/{c['id']}/documents", headers=t, files={"file": ("virus.exe", b"MZ", "application/octet-stream")})
    assert bad.status_code == 415
    ok = client.post(f"/teacher/classes/{c['id']}/documents", headers=t, files={"file": ("Dao_ham.pdf", b"%PDF-1.4", "application/pdf")})
    assert ok.status_code == 201 and ok.json()["status"] == "processing"
    assert client.get(f"/files/documents/{ok.json()['id']}", headers=t).content == b"%PDF-1.4"


# ---------- Rule 2: cách ly giữa các lớp ----------
def test_student_of_class_a_cannot_read_class_b(client):
    t = register(client, "t@x.vn", "teacher")
    a_cls, b_cls = make_class(client, t, "Lớp A"), make_class(client, t, "Lớp B")
    asg_b = make_assignment(client, t, b_cls["id"])
    doc_b = client.post(f"/teacher/classes/{b_cls['id']}/documents", headers=t,
                        files={"file": ("B.pdf", b"%PDF", "application/pdf")}).json()
    hs = register(client, "hs@x.vn", "student")
    client.post("/student/join", json={"class_code": a_cls["class_code"]}, headers=hs)
    assert client.get(f"/student/classes/{b_cls['id']}", headers=hs).status_code == 403
    assert client.get(f"/student/assignments/{asg_b['id']}", headers=hs).status_code == 403
    assert client.post(f"/student/assignments/{asg_b['id']}/submit", data={"content": "x"}, headers=hs).status_code == 403
    assert client.get(f"/files/documents/{doc_b['id']}", headers=hs).status_code == 403
    assert all(x["class_id"] != b_cls["id"] for x in client.get("/student/home", headers=hs).json()["upcoming"])


def test_student_never_sees_reference_answer(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    a = make_assignment(client, t, c["id"])
    hs = register(client, "hs@x.vn", "student")
    client.post("/student/join", json={"class_code": c["class_code"]}, headers=hs)
    view = client.get(f"/student/assignments/{a['id']}", headers=hs).json()
    assert view["assignment"]["reference_answer"] is None
    assert client.get(f"/teacher/assignments/{a['id']}", headers=t).json()["reference_answer"]


# ---------- Rule 5: nộp bài khoá, phiên bản đề ----------
def test_submit_locks_and_keeps_version(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    a = make_assignment(client, t, c["id"])
    hs = register(client, "hs@x.vn", "student")
    client.post("/student/join", json={"class_code": c["class_code"]}, headers=hs)
    r = client.post(f"/student/assignments/{a['id']}/submit", headers=hs, data={"content": "y' = 5(...)"},
                    files={"image": ("vo.jpg", b"\xff\xd8\xff fake", "image/jpeg")})
    assert r.status_code == 201, r.text
    assert r.json()["locked"] and r.json()["has_image"] and r.json()["assignment_version"] == 1
    assert client.post(f"/student/assignments/{a['id']}/submit", headers=hs, data={"content": "sửa"}).status_code == 409
    # Giáo viên sửa đề → v2, bài nộp vẫn gắn v1
    upd = client.put(f"/teacher/assignments/{a['id']}", headers=t, json={"title": "Bài tập 3 (sửa)", "prompt": "Đề mới"})
    assert upd.json()["version"] == 2
    res = client.get(f"/student/assignments/{a['id']}/result", headers=hs).json()
    assert res["submission"]["assignment_version"] == 1
    rows = client.get(f"/teacher/assignments/{a['id']}/submissions", headers=t).json()
    assert rows[0]["status"] == "submitted"


def test_late_submission_rules(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    late_ok = make_assignment(client, t, c["id"], due=PAST, allow_late=True)
    closed = make_assignment(client, t, c["id"], due=PAST, allow_late=False)
    hs = register(client, "hs@x.vn", "student")
    client.post("/student/join", json={"class_code": c["class_code"]}, headers=hs)
    assert client.post(f"/student/assignments/{closed['id']}/submit", headers=hs, data={"content": "x"}).status_code == 403
    r = client.post(f"/student/assignments/{late_ok['id']}/submit", headers=hs, data={"content": "x"})
    assert r.json()["is_late"] is True
    rows = client.get(f"/teacher/assignments/{late_ok['id']}/submissions", headers=t).json()
    assert rows[0]["status"] == "late"


def test_empty_submission_and_bad_image(client):
    t = register(client, "t@x.vn", "teacher")
    c = make_class(client, t)
    a = make_assignment(client, t, c["id"])
    hs = register(client, "hs@x.vn", "student")
    client.post("/student/join", json={"class_code": c["class_code"]}, headers=hs)
    assert client.post(f"/student/assignments/{a['id']}/submit", headers=hs, data={"content": "  "}).status_code == 400
    bad = client.post(f"/student/assignments/{a['id']}/submit", headers=hs, files={"image": ("x.gif", b"GIF89a", "image/gif")})
    assert bad.status_code == 415


# ---------- Rule 4: chỉ thấy điểm sau khi giáo viên công bố ----------
def test_result_hidden_until_published(client):
    t = register(client, "t@x.vn", "teacher")
    t2 = register(client, "t2@x.vn", "teacher")
    c = make_class(client, t)
    a = make_assignment(client, t, c["id"])
    hs = register(client, "hs@x.vn", "student")
    client.post("/student/join", json={"class_code": c["class_code"]}, headers=hs)
    sub = client.post(f"/student/assignments/{a['id']}/submit", headers=hs, data={"content": "bài làm"}).json()
    assert client.get(f"/student/assignments/{a['id']}/result", headers=hs).json()["published"] is False
    assert client.post(f"/teacher/grades/{sub['id']}/publish", headers=t2, json={"score": 10}).status_code == 403
    client.post(f"/teacher/grades/{sub['id']}/publish", headers=t, json={"score": 8.5, "feedback": "Tốt"})
    res = client.get(f"/student/assignments/{a['id']}/result", headers=hs).json()
    assert res["published"] and res["score"] == 8.5 and res["feedback"] == "Tốt"
