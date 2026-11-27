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
from fractions import Fraction

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


_LEAK_DECIMAL = r"[+-]?(?:\d{1,18}(?:\.\d{1,12})?|\.\d{1,12})"
_LEAK_NUMBER = _LEAK_DECIMAL + r"(?:/" + _LEAK_DECIMAL + r")?"
_LEAK_VALUE = r"(?:±\s*)?" + _LEAK_NUMBER
_LEAK_ROOT = r"(?<![\w^])x(?:_?\{?\d{1,2}\}?)?\s*(?:=|≠|bang\b|khac\b|la\b)\s*"
_LEAK_TOKEN = re.compile(r"(?<![\w.\d/])(" + _LEAK_VALUE + r")(?![\w\d/]|\.\d)")
_LEAK_EMPTY = re.compile(r"\bvo nghiem\b|\bkhong co nghiem(?: thuc)?\b|\bs\s*=\s*(?:∅|\{\s*\})")


def _leak_normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    text = strip_accents(text).translate(str.maketrans({"−": "-", "–": "-", "﹣": "-", "÷": "/", "⁄": "/", "∕": "/", "×": "*", "·": "*"}))
    text = re.sub(r"\\(?:times|cdot)\b", "*", text)
    text = re.sub(r"\\(?:pm|mp)\b", "±", text).replace("∓", "±")
    text = re.sub(r"\\(?:in)\b", "∈", text)
    text = re.sub(r"\\(?:dfrac|tfrac|frac)\s*\{\s*(" + _LEAK_DECIMAL + r")\s*\}\s*\{\s*(" + _LEAK_DECIMAL + r")\s*\}", r"\1/\2", text)
    text = re.sub(r"\\(?:left|right|quad|qquad)\b|\\[!,;:]", " ", text)
    text = re.sub(r"\\([(){}\[\]])", r"\1", text).replace("$", "")
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"(?<=[+-])\s+(?=[\d.])", "", text)
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\(\s*(" + _LEAK_NUMBER + r")\s*\)", r"\1", text)
    return text


def _leak_fraction(value):
    try:
        parts = value.split("/")
        return Fraction(parts[0]) / Fraction(parts[1]) if len(parts) == 2 else Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def _leak_values(text, roots_only):
    """Read exact numeric literals, excluding prefixes of a larger expression."""
    values = set()
    if roots_only:
        spans = []
        for match in re.finditer(_LEAK_ROOT + r"(" + _LEAK_VALUE + r"(?:\s*=\s*" + _LEAK_VALUE + r")*)", text):
            spans.extend((match.start(1) + token.start(1), match.start(1) + token.end(1)) for token in _LEAK_TOKEN.finditer(match[1]))
        for marker in re.finditer(r"\bnghiem(?:\s+(?:kep|phan biet|thuc|cua phuong trinh|lan luot))*\s*(?:la|:|=)\s*|\bdap\s+(?:an|so)(?:\s+cuoi)?\s*(?:la|:|=)\s*|\bs\s*=\s*\{|\bx\s*∈\s*\{", text):
            tail = text[marker.end():]
            listing = re.match(r"(" + _LEAK_VALUE + r")(?:(?:\s*(?:;|,|va\b|hoac\b)\s*)(" + _LEAK_VALUE + r"))*", tail)
            if listing:
                spans.extend((marker.end() + m.start(1), marker.end() + m.end(1)) for m in _LEAK_TOKEN.finditer(listing[0]))
    else:
        spans = [m.span(1) for m in _LEAK_TOKEN.finditer(text)]
    for start, end in spans:
        # Do not read x=2 as a final root when it is x=20, x=2a or x=2+1.
        suffix = text[end:]
        if re.match(r"(?:[\w\d/]|\.\d)", suffix) or re.match(r"\s*[+*/^(]", suffix):
            continue
        if re.match(r"\s*-\s*[\d(]", suffix):
            continue
        literal = text[start:end].strip()
        plus_minus = literal.startswith("±")
        value = _leak_fraction(literal[1:].strip() if plus_minus else literal)
        if value is not None:
            values.add(value)
            if plus_minus:
                values.add(-value)
    return values


def _leak_empty_solution(text):
    for match in _LEAK_EMPTY.finditer(text):
        prefix = re.split(r"[.!?;\n]", text[:match.start()])[-1]
        if re.search(r"\b(?:chua|neu|khong the|khong phai|khong duoc)\b", prefix):
            continue
        return True
    return False


@tool
def check_leak(reply: str, final_answers: list) -> dict:
    """check_leak · Input: reply, các dạng đáp án cuối · Output: {leaked: bool, matches: [str]}.
    Chỉ đọc và tính toán, không tác động ra ngoài. Owner: Thắng, T-02.

    So số hữu tỉ chính xác trong ngữ cảnh x, nghiệm hoặc tập nghiệm; đáp án vô hướng
    được so theo token số đầy đủ. matches giữ nguyên các chuỗi trong final_answers.
    Một nghiệm đúng được nêu dù dưới dạng câu hỏi vẫn bị chặn để tránh tiết lộ.
    Dấu phẩy giữa hai chữ số được hiểu là dấu thập phân; tách nghiệm bằng ; hoặc và.
    Đây không phải bộ chứng minh toán học: chưa nhận diễn đạt gián tiếp, nghiệm vô tỉ,
    biểu thức tương đương phức tạp hoặc mã hóa. Không bảo đảm chống lộ tuyệt đối.
    """
    normalized = _leak_normalize(reply)
    roots = _leak_values(normalized, roots_only=True)
    scalars = _leak_values(normalized, roots_only=False)
    if re.fullmatch(r"\s*" + _LEAK_NUMBER + r"\s*[.!]?\s*", normalized):
        roots.update(scalars)
    matches = []
    for answer in final_answers:
        if not isinstance(answer, str) or not answer.strip():
            continue
        candidate = _leak_normalize(answer).strip()
        if _LEAK_EMPTY.search(candidate):
            matched = _leak_empty_solution(normalized)
        else:
            wanted = _leak_values(candidate, roots_only=True)
            if wanted:
                matched = bool(wanted & roots)
            elif re.fullmatch(_LEAK_NUMBER, candidate):
                matched = _leak_fraction(candidate) in scalars
            else:
                # Non-numeric literal answers retain the original contract.
                matched = bool(re.search(r"(?<!\w)" + re.escape(candidate) + r"(?!\w)", normalized))
        if matched:
            matches.append(answer)
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
