"""Công cụ của gia sư MinutesStudy Tutor.

Mỗi hàm có @tool để khung ghi trace. Docstring ghi: tên · input · output · có tác động ra ngoài không.
Không công cụ nào tác động ra ngoài: tất cả chỉ đọc data/ hoặc tính bằng code.

HỢP ĐỒNG (giữ nguyên chữ ký để 4 người làm song song, xem TICKETS.md):
    get_assignment(assignment_id, now)  -> dict | None   (answer_key, final_answers CHỈ có khi đã hết hạn)
    get_tutor_mode(role, due_at, now)   -> "hint" | "answer"
    search_lesson(query, class_id, k)   -> [{"code","page","title","text","score"}]
    check_leak(reply, final_answers)    -> {"leaked": bool, "matches": [str]}
    citations(reply, chunks)            -> {"reply": str, "sources": [{"code","page"}]}

Bản hiện tại là v0 chạy được, đơn giản. Ai phụ trách thay bằng bản thật theo ticket ghi trong từng hàm.
"""
import json
import os
import re
import unicodedata
from datetime import datetime, timezone

from tracing import tool, TOOLS  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def _load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def _parse_dt(s):
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def strip_accents(s: str) -> str:
    """Bỏ dấu tiếng Việt + chữ thường, dùng chung cho tìm kiếm và so đáp án."""
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


@tool
def get_assignment(assignment_id: str, now: str) -> dict:
    """get_assignment · Input: mã bài tập, giờ hỏi (ISO) · Output: đề, hạn, lớp, mã đoạn liên quan;
    answer_key + final_answers CHỈ trả khi đã hết hạn (Rule 3 trong app/docs/rules.md) · Không tác động ra ngoài.
    Owner: Thắng (dữ liệu thật ở data/assignments.json, ticket T-01)."""
    for a in _load("assignments.json"):
        if a["id"] == assignment_id:
            out = {k: a[k] for k in ("id", "class_id", "title", "question", "due_at", "lesson_codes")}
            if _parse_dt(now) >= _parse_dt(a["due_at"]):
                out["answer_key"] = a["answer_key"]
            return out
    return None


@tool
def get_passages(codes: list) -> list:
    """get_passages · Input: danh sách mã đoạn (vd lesson_codes của bài tập) · Output: các đoạn tài liệu kèm trang ·
    Không tác động ra ngoài. Dùng để luôn đưa đúng phần bài giảng của bài tập vào ngữ cảnh. Owner: Khoa (K-02)."""
    want = set(codes or [])
    return [dict(p, score=0) for p in _load("lesson.json") if p["code"] in want]


def final_answers_of(assignment_id: str) -> list:
    """Chỉ dùng cho chốt chặn check_leak trong code. KHÔNG bao giờ đưa vào prompt khi bài còn hạn."""
    for a in _load("assignments.json"):
        if a["id"] == assignment_id:
            return a.get("final_answers", [])
    return []


@tool
def get_tutor_mode(role: str, due_at: str, now: str) -> str:
    """get_tutor_mode · Input: vai (lấy từ tài khoản, không từ lời nhắn), hạn nộp, giờ máy chủ ·
    Output: "hint" (còn hạn, học sinh) hoặc "answer" · Không tác động ra ngoài.
    Cùng logic với app/backend/app/agents/policy.py. Owner: Ninh (ticket N-01)."""
    if role != "student":
        return "answer"
    return "answer" if _parse_dt(now) >= _parse_dt(due_at) else "hint"


@tool
def search_lesson(query: str, class_id: str, k: int = 3) -> list:
    """search_lesson · Input: câu hỏi, mã lớp, số đoạn · Output: đoạn tài liệu kèm trang, LỌC CỨNG theo lớp ·
    Không tác động ra ngoài.
    v0: đếm từ trùng (không dấu). Owner: Ninh thay bằng BM25 không dấu, tham khảo app/backend/app/core/tenancy.py (ticket N-02)."""
    q = set(re.findall(r"\w+", strip_accents(query)))
    scored = []
    for p in _load("lesson.json"):
        if p["class_id"] != class_id:
            continue
        words = set(re.findall(r"\w+", strip_accents(p["title"] + " " + p["text"])))
        score = len(q & words)
        if score:
            scored.append(dict(p, score=score))
    scored.sort(key=lambda x: -x["score"])
    return scored[:k]


@tool
def check_leak(reply: str, final_answers: list) -> dict:
    """check_leak · Input: câu trả lời của AI, các dạng đáp án cuối · Output: {"leaked", "matches"} ·
    Không tác động ra ngoài. CHỐT CHẶN BẰNG CODE: chế độ hint mà leaked=True thì agent không được trả câu đó.
    v0: so chuỗi sau khi bỏ dấu, bỏ khoảng trắng. Owner: Thắng làm bản chắc hơn (số, phân số, "x bằng 2"…) (ticket T-02)."""
    norm = lambda s: re.sub(r"\s+", "", strip_accents(s))  # noqa: E731
    r = norm(reply)
    matches = [a for a in final_answers if a and norm(a) in r]
    return {"leaked": bool(matches), "matches": matches}


@tool
def citations(reply: str, chunks: list) -> dict:
    """citations · Input: câu trả lời, các đoạn đã tìm · Output: câu trả lời đã bỏ thẻ nguồn bịa + danh sách nguồn thật ·
    Không tác động ra ngoài. Thẻ nguồn dạng [Nguồn: T10-C3-P02 - Trang 2].
    Tham khảo app/backend/app/agents/tutor.py (citations). Owner: Ninh (ticket N-03)."""
    valid = {c["code"]: c["page"] for c in chunks}
    sources = []

    def keep(m):
        code = m.group(1).strip()
        if code in valid:
            sources.append({"code": code, "page": valid[code]})
            return m.group(0)
        return ""  # thẻ nguồn bịa → bỏ

    clean = re.sub(r"\[Nguồn:\s*([^\]\-]+?)\s*-\s*Trang\s*\d+\]", keep, reply)
    return {"reply": clean, "sources": sources}
