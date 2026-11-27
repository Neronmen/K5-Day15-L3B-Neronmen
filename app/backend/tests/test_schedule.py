"""Thông báo lớp (báo nghỉ / học bù), lịch học hằng tuần, file đề bài tập."""
from datetime import date, timedelta

from tests.conftest import register
from tests.test_ai import DOCX, make_docx
from tests.test_phase1 import make_assignment, make_class


def setup_class(client):
    t = register(client, "gv@x.vn", "teacher")
    s = register(client, "hs@x.vn", "student")
    c = make_class(client, t)
    assert client.post("/student/join", json={"class_code": c["class_code"]}, headers=s).status_code == 200
    return t, s, c


def next_weekday(wd: int) -> date:
    d = date.today() + timedelta(days=1)
    while d.weekday() != wd:
        d += timedelta(days=1)
    return d


def test_sessions_calendar_and_clash(client):
    t, s, c = setup_class(client)
    r = client.post(f"/teacher/classes/{c['id']}/sessions", headers=t,
                    json={"weekday": 1, "start_time": "18:00", "end_time": "19:30", "room": "P.204"})
    assert r.status_code == 201, r.text
    # Giờ kết thúc trước giờ bắt đầu
    assert client.post(f"/teacher/classes/{c['id']}/sessions", headers=t,
                       json={"weekday": 2, "start_time": "10:00", "end_time": "09:00"}).status_code == 422
    # Lớp khác của cùng giáo viên trùng giờ
    c2 = make_class(client, t, "Toán 12")
    r2 = client.post(f"/teacher/classes/{c2['id']}/sessions", headers=t,
                     json={"weekday": 1, "start_time": "19:00", "end_time": "20:00"})
    assert r2.status_code == 409 and "Trùng giờ" in r2.json()["detail"]

    start = next_weekday(0)
    cal = client.get(f"/student/calendar?start={start}&days=14", headers=s).json()
    assert [x["date"] for x in cal] == [str(start + timedelta(days=1)), str(start + timedelta(days=8))]
    assert cal[0]["room"] == "P.204" and cal[0]["cancelled"] is False
    dash = client.get("/teacher/dashboard", headers=t).json()
    assert dash[0]["schedule_text"] == "T3 18:00–19:30" and dash[0]["next_session_at"]


def test_cancel_and_makeup_announcements(client):
    t, s, c = setup_class(client)
    sess = client.post(f"/teacher/classes/{c['id']}/sessions", headers=t,
                       json={"weekday": 3, "start_time": "07:00", "end_time": "08:30"}).json()
    day = next_weekday(3)
    # Ngày nghỉ không đúng thứ của buổi học
    bad = client.post(f"/teacher/classes/{c['id']}/announcements", headers=t, json={
        "kind": "cancel", "title": "Nghỉ", "event_date": str(day + timedelta(days=1)), "session_id": sess["id"]})
    assert bad.status_code == 422
    r = client.post(f"/teacher/classes/{c['id']}/announcements", headers=t, json={
        "kind": "cancel", "title": "Nghỉ học thứ 5 do cô đi tập huấn", "event_date": str(day), "session_id": sess["id"]})
    assert r.status_code == 201, r.text
    cancel_id = r.json()["id"]
    assert client.post(f"/teacher/classes/{c['id']}/announcements", headers=t, json={
        "kind": "makeup", "title": "Học bù", "event_date": str(day + timedelta(days=2)), "event_start": "14:00"}).status_code == 422
    assert client.post(f"/teacher/classes/{c['id']}/announcements", headers=t, json={
        "kind": "makeup", "title": "Học bù thứ 7", "event_date": str(day + timedelta(days=2)),
        "event_start": "14:00", "event_end": "15:30"}).status_code == 201

    cal = client.get(f"/student/calendar?start={day}&days=3", headers=s).json()
    assert [(x["kind"], x["cancelled"]) for x in cal] == [("regular", True), ("makeup", False)]
    assert cal[0]["note"] == "Nghỉ học thứ 5 do cô đi tập huấn"

    # Học sinh nhận thông báo và thấy trên trang lớp / trang chủ
    notes = client.get("/notifications", headers=s).json()
    assert {n["kind"] for n in notes} == {"announcement"} and len(notes) == 2
    view = client.get(f"/student/classes/{c['id']}", headers=s).json()
    assert len(view["announcements"]) == 2 and view["sessions"][0]["weekday"] == 3
    assert len(client.get("/student/home", headers=s).json()["announcements"]) == 2

    # Xoá báo nghỉ → buổi học trở lại bình thường
    assert client.delete(f"/teacher/announcements/{cancel_id}", headers=t).status_code == 204
    cal = client.get(f"/student/calendar?start={day}&days=1", headers=s).json()
    assert cal[0]["cancelled"] is False


def test_announcement_pin_and_isolation(client):
    t, s, c = setup_class(client)
    a = client.post(f"/teacher/classes/{c['id']}/announcements", headers=t,
                    json={"title": "Mang máy tính bỏ túi", "body": "Tiết sau kiểm tra 15 phút"}).json()
    b = client.post(f"/teacher/classes/{c['id']}/announcements", headers=t, json={"title": "Tin sau"}).json()
    client.patch(f"/teacher/announcements/{a['id']}", headers=t, json={"pinned": True})
    view = client.get(f"/student/classes/{c['id']}", headers=s).json()
    assert [x["id"] for x in view["announcements"]] == [a["id"], b["id"]]

    # Giáo viên khác và học sinh không được sửa / xem lớp không phải của mình
    t2 = register(client, "gv2@x.vn", "teacher")
    s2 = register(client, "hs2@x.vn", "student")
    assert client.patch(f"/teacher/announcements/{a['id']}", headers=t2, json={"title": "x"}).status_code == 403
    assert client.post(f"/teacher/classes/{c['id']}/announcements", headers=t2, json={"title": "x"}).status_code == 403
    assert client.post(f"/teacher/classes/{c['id']}/announcements", headers=s, json={"title": "x"}).status_code == 403
    assert client.get(f"/student/classes/{c['id']}", headers=s2).status_code == 403
    assert client.get("/student/calendar", headers=s2).json() == []


def test_assignment_attachment(client, monkeypatch):
    t, s, c = setup_class(client)
    a = make_assignment(client, t, c["id"])
    bad = client.post(f"/teacher/assignments/{a['id']}/attachment", headers=t, files={"file": ("de.txt", b"x", "text/plain")})
    assert bad.status_code == 415
    r = client.post(f"/teacher/assignments/{a['id']}/attachment", headers=t,
                    files={"file": ("De_kiem_tra.docx", make_docx(["Câu 1: Tính đạo hàm y = sin(3x)"]), DOCX)})
    assert r.status_code == 200, r.text
    assert r.json()["attachment_name"] == "De_kiem_tra.docx"

    detail = client.get(f"/student/assignments/{a['id']}", headers=s).json()
    assert detail["assignment"]["attachment_name"] == "De_kiem_tra.docx"
    f = client.get(f"/files/assignments/{a['id']}/attachment", headers=s)
    assert f.status_code == 200 and f.content[:2] == b"PK"
    outsider = register(client, "hs9@x.vn", "student")
    assert client.get(f"/files/assignments/{a['id']}/attachment", headers=outsider).status_code == 403

    # Chữ trong file đề được đưa cho AI chấm
    from app.db import SessionLocal
    from app.models import Assignment
    with SessionLocal() as db:
        full = db.get(Assignment, a["id"]).full_prompt("Đề gõ tay")
    assert "Đề gõ tay" in full and "sin(3x)" in full

    assert client.delete(f"/teacher/assignments/{a['id']}/attachment", headers=t).json()["attachment_name"] is None
    assert client.get(f"/files/assignments/{a['id']}/attachment", headers=s).status_code == 404
