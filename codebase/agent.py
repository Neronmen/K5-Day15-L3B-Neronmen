"""Luồng chính của MinutesStudy Tutor — workflow cố định (xem spec.md §4). Owner: Khoa (ticket K-02).

`python run.py`, `run.py eval`, `run.py simulate` đều gọi answer(text).

INPUT: ô input của câu thử là một JSON:
    {"assignment_id": "BT01", "role": "student", "asked_at": "2026-11-28T21:00:00+07:00",
     "message": "Em tính Delta = 25 + 24 = 49 rồi bí"}
    Gõ chữ thường (không phải JSON) ở `python run.py` thì dùng mặc định DEFAULTS bên dưới.
OUTPUT: {"output": str}. Dòng đầu luôn là nhãn [QUYET_DINH: ...] (xem prompts.py).

Luồng:
    get_assignment → get_tutor_mode (code) → search_lesson (lọc lớp)
    → không có đoạn liên quan & không phải câu về bài tập → KHONG_CO (không gọi model)
    → call_model → citations (bỏ nguồn bịa) → check_leak (code) → lộ thì sinh lại 1 lần → vẫn lộ thì câu cố định
"""
import json

from ai import call_model
from prompts import NOT_FOUND, SYSTEM_ANSWER, SYSTEM_HINT
from tools import check_leak, citations, final_answers_of, get_assignment, get_tutor_mode, search_lesson
from tracing import note

DEFAULTS = {"assignment_id": "BT01", "role": "student", "asked_at": "2026-11-28T21:00:00+07:00"}
SAFE_HINT = ("[QUYET_DINH: GOI_Y]\nMình chưa thể đưa kết quả khi bài còn hạn nộp. "
             "Em gửi bước em đang làm, mình chỉ ra chỗ cần xem lại nhé.")


def parse_input(text: str) -> dict:
    try:
        req = json.loads(text)
        if isinstance(req, dict) and "message" in req:
            return {**DEFAULTS, **req}
    except (json.JSONDecodeError, TypeError):
        pass
    return {**DEFAULTS, "message": text}


def answer(text: str) -> dict:
    req = parse_input(text)
    asg = get_assignment(req["assignment_id"], req["asked_at"])
    if asg is None:
        return {"output": "[QUYET_DINH: KHONG_CO]\nMình không tìm thấy bài tập này trong lớp của em."}

    mode = get_tutor_mode(req["role"], asg["due_at"], req["asked_at"])
    chunks = search_lesson(req["message"] + " " + asg["question"], asg["class_id"])
    if not chunks:
        note("không có đoạn tài liệu liên quan → KHONG_CO, không gọi model")
        return {"output": "[QUYET_DINH: KHONG_CO]\n" + NOT_FOUND}

    docs = "\n".join("[%s - Trang %s] %s: %s" % (c["code"], c["page"], c["title"], c["text"]) for c in chunks)
    user = "TÀI LIỆU:\n%s\n\nĐỀ BÀI: %s\n" % (docs, asg["question"])
    if mode == "answer" and "answer_key" in asg:
        user += "ĐÁP ÁN MẪU: %s\n" % asg["answer_key"]
    user += "\nTIN NHẮN HỌC SINH:\n<<<\n%s\n>>>" % req["message"]
    system = SYSTEM_HINT if mode == "hint" else SYSTEM_ANSWER

    reply = citations(call_model(system, user)["text"], chunks)["reply"]
    if mode == "hint":
        finals = final_answers_of(asg["id"])
        if check_leak(reply, finals)["leaked"]:
            note("lộ đáp án ở lần 1 → sinh lại")
            retry = call_model(system + "\nLẦN TRƯỚC BẠN ĐÃ LỘ ĐÁP ÁN. Chỉ gợi ý, không nêu kết quả.", user)
            reply = citations(retry["text"], chunks)["reply"]
            if check_leak(reply, finals)["leaked"]:
                note("vẫn lộ ở lần 2 → trả câu cố định")
                reply = SAFE_HINT
    return {"output": reply}
