"""Trợ lý AI giáo viên: tìm kiếm & tổng hợp tài liệu nhiều lớp, cách ly giữa giáo viên, lưu thành tài liệu lớp."""
from app.core.config import settings
from tests.conftest import register
from tests.test_ai import DOCX, LECTURE_PAGES, fake_llm, make_docx, sse_events  # noqa: F401 - fixture

PHYSICS = ["Định luật II Newton: F = m·a, gia tốc tỉ lệ thuận với lực.", "Động lượng p = m·v được bảo toàn trong hệ kín."]


def teacher_with_two_classes(client):
    t = register(client, "gv@x.vn", "teacher")
    math = client.post("/teacher/classes", json={"name": "Toán 11", "subject": "Toán"}, headers=t).json()
    phys = client.post("/teacher/classes", json={"name": "Lý 10", "subject": "Vật lý"}, headers=t).json()
    d1 = client.post(f"/teacher/classes/{math['id']}/documents", headers=t,
                     files={"file": ("Dao_ham.docx", make_docx(LECTURE_PAGES), DOCX)}).json()
    d2 = client.post(f"/teacher/classes/{phys['id']}/documents", headers=t,
                     files={"file": ("Newton.docx", make_docx(PHYSICS), DOCX)}).json()
    return t, math, phys, d1, d2


def test_search_across_classes_and_scope(client):
    t, math, phys, d1, d2 = teacher_with_two_classes(client)
    src = client.get("/teacher/assistant/sources", headers=t).json()
    assert {c["name"]: len(c["documents"]) for c in src} == {"Lý 10": 1, "Toán 11": 1}

    hits = client.post("/teacher/assistant/search", headers=t, json={"query": "dao ham ham hop"}).json()
    assert hits and hits[0]["file_name"] == "Dao_ham.docx" and hits[0]["class_name"] == "Toán 11"
    assert "hàm hợp" in hits[0]["snippet"]
    # Giới hạn trong lớp Lý: không thấy tài liệu Toán
    only_phys = client.post("/teacher/assistant/search", headers=t,
                            json={"query": "dao ham dong luong", "class_ids": [phys["id"]]}).json()
    assert {h["file_name"] for h in only_phys} == {"Newton.docx"}


def test_other_teacher_cannot_search_or_read(client):
    t, math, phys, d1, d2 = teacher_with_two_classes(client)
    other = register(client, "gv2@x.vn", "teacher")
    assert client.post("/teacher/assistant/search", headers=other, json={"query": "dao ham"}).json() == []
    assert client.post("/teacher/assistant/search", headers=other,
                       json={"query": "dao ham", "class_ids": [math["id"]]}).status_code == 403
    assert client.get(f"/teacher/assistant/documents/{d1['id']}/pages", headers=other).status_code == 403
    hs = register(client, "hs@x.vn", "student")
    assert client.post("/teacher/assistant/search", headers=hs, json={"query": "dao ham"}).status_code == 403


def test_chat_cites_sources_and_whole_document_summary(client, fake_llm):
    t, math, phys, d1, d2 = teacher_with_two_classes(client)
    fake_llm["answer"] = "Quy tắc dây chuyền [Nguồn: Dao_ham.docx - Phần 2]. Sách lạ [Nguồn: Bia.pdf - Trang 3]."
    r = client.post("/teacher/assistant/chat", headers=t, json={"question": "Tìm phần đạo hàm hàm hợp", "task": "ask"})
    ev = sse_events(r.text)
    assert ev[-1]["type"] == "done"
    assert [c["label"] for c in ev[-1]["citations"]] == ["Dao_ham.docx - Phần 2"]  # nguồn bịa bị loại
    system = fake_llm["stream"][-1]["system"]
    assert "hàm hợp" in system and 'lop="Toán 11"' in system

    # Tóm tắt cả tài liệu: đưa mọi trang của tài liệu được chọn, không chỉ vài đoạn tìm được
    client.post("/teacher/assistant/chat", headers=t,
                json={"question": "Tóm tắt", "task": "summary", "document_ids": [d1["id"]]})
    system = fake_llm["stream"][-1]["system"]
    assert all(p[:20] in system for p in LECTURE_PAGES) and "Newton" not in system
    assert "ĐỀ CƯƠNG" not in system and "Tóm tắt nội dung tài liệu" in system

    hist = client.get("/teacher/assistant/history", headers=t).json()
    assert [m["role"] for m in hist] == ["user", "assistant", "user", "assistant"]
    # Lịch sử riêng từng giáo viên
    other = register(client, "gv2@x.vn", "teacher")
    assert client.get("/teacher/assistant/history", headers=other).json() == []
    assert client.delete("/teacher/assistant/history", headers=t).status_code == 204
    assert client.get("/teacher/assistant/history", headers=t).json() == []


def test_document_of_other_class_rejected_and_quota(client, fake_llm, monkeypatch):
    t, math, phys, d1, d2 = teacher_with_two_classes(client)
    r = client.post("/teacher/assistant/chat", headers=t,
                    json={"question": "Tóm tắt", "task": "summary", "class_ids": [math["id"]], "document_ids": [d2["id"]]})
    assert r.status_code == 404
    monkeypatch.setattr(settings, "teacher_ai_daily_limit", 1)
    assert client.post("/teacher/assistant/chat", headers=t, json={"question": "a"}).status_code == 200
    assert client.post("/teacher/assistant/chat", headers=t, json={"question": "b"}).status_code == 429


def test_save_summary_as_class_document(client):
    t, math, phys, d1, d2 = teacher_with_two_classes(client)
    r = client.post("/teacher/assistant/save", headers=t, json={
        "class_id": math["id"], "title": "Đề cương ôn tập Đạo hàm",
        "content": "## Kiến thức cần nhớ\n- Quy tắc dây chuyền: y' = f'(u)·u'"})
    assert r.status_code == 201, r.text
    assert r.json()["file_name"] == "De_cuong_on_tap_Dao_ham.md"
    docs = client.get(f"/teacher/classes/{math['id']}/documents", headers=t).json()
    saved = next(d for d in docs if d["id"] == r.json()["id"])
    assert saved["status"] == "ready"  # đã bóc tách xong → học sinh đọc được, AI lớp dùng làm nguồn
    hits = client.post("/teacher/assistant/search", headers=t,
                       json={"query": "quy tac day chuyen", "document_ids": [saved["id"]]}).json()
    assert hits and hits[0]["file_name"] == "De_cuong_on_tap_Dao_ham.md"
    other = register(client, "gv2@x.vn", "teacher")
    assert client.post("/teacher/assistant/save", headers=other,
                       json={"class_id": math["id"], "title": "x", "content": "y"}).status_code == 403
