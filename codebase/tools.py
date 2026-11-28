"""Công cụ của gia sư MinutesStudy Tutor.

Mỗi hàm có @tool để khung ghi trace. Docstring ghi: tên · input · output · có tác động ra ngoài không.
Không công cụ nào tác động ra ngoài: tất cả chỉ đọc data/ hoặc tính bằng code.

HỢP ĐỒNG (giữ nguyên chữ ký để 4 người làm song song, xem TICKETS.md):
    get_assignment(assignment_id, now)  -> dict | None   (answer_key, final_answers CHỈ có khi đã hết hạn)
    get_tutor_mode(role, due_at, now)   -> "hint" | "answer"
    search_lesson(query, class_id, k)   -> [{"code","page","title","text","score"}]
    check_leak(reply, final_answers)    -> {"leaked": bool, "matches": [str]}
    citations(reply, chunks)            -> {"reply": str, "sources": [{"code","page"}]}
    flag_message(message, mode)         -> "jailbreak" | "impersonation" | "ask_answer" | None   (N-03, chỉ gắn cờ)
    check_open_assignments(message, class_id, now, exclude_id) -> {"matches": [...], "final_answers": [...]}

Bản hiện tại là v0 chạy được, đơn giản. Ai phụ trách thay bằng bản thật theo ticket ghi trong từng hàm.
"""
import json
import math
import os
import re
from collections import Counter
import unicodedata
from datetime import datetime, timezone
from fractions import Fraction

from tracing import note, tool, TOOLS  # noqa: F401

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


def open_finals_of(class_id: str, now: str, exclude_id: str) -> list:
    """Đáp án cuối của các bài CÒN HẠN khác trong cùng lớp (mỗi bài một list). Chỉ dùng cho chốt chặn check_leak
    bằng code, KHÔNG bao giờ đưa vào prompt. Không tác động ra ngoài."""
    t = _parse_dt(now)
    return [a.get("final_answers", []) for a in _load("assignments.json")
            if a["class_id"] == class_id and a["id"] != exclude_id and _parse_dt(a["due_at"]) > t]


@tool
def get_tutor_mode(role: str, due_at: str, now: str) -> str:
    """get_tutor_mode · Input: vai (lấy từ tài khoản, không từ lời nhắn), hạn nộp, giờ máy chủ ·
    Output: "hint" (còn hạn, học sinh) hoặc "answer" · Không tác động ra ngoài.
    Cùng logic với app/backend/app/agents/policy.py (giáo viên luôn "answer"; học sinh "answer" khi now >= due_at,
    đúng lúc hết hạn cũng tính là hết hạn). Owner: Ninh (ticket N-01).

    Khác policy.py ở chỗ ĐÓNG KHI LỖI: policy.py coi mọi vai != "student" là giáo viên; ở đây chỉ vai nằm trong
    ANSWER_ROLES mới luôn được "answer". Vai trống / lạ / viết hoa sai, hạn hoặc giờ hỏng → xử như học sinh,
    hỏng giờ → "hint". Lý do: input câu thử là JSON, sai một chữ ở `role` không được làm lộ đáp án."""
    if (role or "").strip().lower() in ANSWER_ROLES:
        return "answer"
    try:
        return "answer" if _parse_dt(now) >= _parse_dt(due_at) else "hint"
    except (TypeError, ValueError):
        return "hint"


ANSWER_ROLES = {"teacher"}  # vai trong app/backend/app/models.py: "teacher" | "student"


@tool
def search_lesson(query: str, class_id: str, k: int = 3) -> list:
    """search_lesson · Input: câu hỏi, mã lớp, số đoạn · Output: đoạn tài liệu kèm trang, LỌC CỨNG theo lớp ·
    Không tác động ra ngoài.
    BM25 (cùng công thức _bm25 trong app/backend/app/core/tenancy.py), chỉ thư viện chuẩn. Owner: Ninh (N-02).
    - LỌC CỨNG theo class_id TRƯỚC khi tính điểm: thống kê IDF cũng chỉ lấy từ tài liệu của lớp đó.
    - Bỏ từ hư ("là", "gì", "em"...), thêm bigram ("biet_thuc"), tiêu đề tính gấp TITLE_WEIGHT lần.
    - So khớp theo dấu: từ học sinh GÕ CÓ DẤU thì so có dấu ("thủ" ≠ "thứ", "quá" ≠ "quả"); từ gõ không dấu thì so
      không dấu ("delta la gi" vẫn khớp). Bỏ dấu toàn bộ như tenancy.py làm "Thủ đô nước Pháp" khớp nhầm "thứ tự".
    - Bỏ số thuần ("25", "49" trong bước làm của học sinh): đó là bài làm, không phải từ khoá tìm kiếm.
    - score = BM25 × độ_phủ², độ phủ = tỉ lệ từ khoá đơn của câu hỏi có trong đoạn; làm tròn 3 chữ số. Câu chỉ trùng
      1/3 từ ("Thủ đô nước Pháp" trùng mỗi "pháp" trong "phương pháp") bị chia 9, nên agent dùng được một ngưỡng
      cố định TUTOR_MIN_SCORE (đề xuất 0.5: câu ngoài bài ≤ 0.26, "Delta là gì" ≥ 0.89 trên cả dữ liệu mẫu lẫn T-01).
    - Chỉ trả đoạn có score > 0, xếp giảm dần (bằng điểm thì trang nhỏ trước).
    Phần chấm điểm nằm ở rank_passages để app/ (N-08) dùng chung trên đoạn bài giảng trong DB."""
    if not class_id:
        return []
    return rank_passages(query, [p for p in _load("lesson.json") if p.get("class_id") == class_id], k)


def rank_passages(query: str, passages: list, k: int = 3) -> list:
    """Chấm điểm BM25 (xem search_lesson) trên danh sách đoạn {"title","text",...} ĐÃ LỌC THEO LỚP từ trước.
    Không đọc file, không lọc lớp: người gọi chịu trách nhiệm lọc tenant (app/ dùng app.core.tenancy)."""
    q = _terms(query)
    if not q or not passages or k <= 0:
        return []
    # Mỗi đoạn có 2 túi từ: có dấu (key "a") và không dấu (key "p"); từ của câu hỏi tra đúng túi của nó.
    docs = []
    for p in passages:
        title, text = _terms(p.get("title", "")), _terms(p.get("text", ""))
        docs.append({f: [t[f] for t in title] * TITLE_WEIGHT + [t[f] for t in text] for f in ("a", "p")})
    n = len(docs)
    avgdl = sum(len(d["p"]) for d in docs) / n or 1
    df = {f: Counter(t for d in docs for t in set(d[f])) for f in ("a", "p")}
    keys = {(t["f"], t[t["f"]]) for t in q}            # (túi, từ) của câu hỏi, đã bỏ trùng
    unigrams = {key for key in keys if "_" not in key[1]}
    scored = []
    for p, d in zip(passages, docs):
        tf = {f: Counter(d[f]) for f in ("a", "p")}
        s, hit = 0.0, 0
        for f, t in keys:
            if not tf[f][t]:
                continue
            hit += (f, t) in unigrams
            idf = math.log(1 + (n - df[f][t] + 0.5) / (df[f][t] + 0.5))
            s += idf * tf[f][t] * (BM25_K1 + 1) / (tf[f][t] + BM25_K1 * (1 - BM25_B + BM25_B * len(d["p"]) / avgdl))
        coverage = hit / len(unigrams) if unigrams else 0
        if s > 0 and coverage > 0:
            scored.append(dict(p, score=round(s * coverage ** 2, 3)))
    scored.sort(key=lambda x: (-x["score"], x.get("page", 0)))
    return scored[:k]


BM25_K1, BM25_B, TITLE_WEIGHT = 1.2, 0.75, 3
# Từ hư trong câu hỏi tiếng Việt (so sau khi bỏ dấu) — bỏ khi chấm điểm. Lấy từ tenancy._STOP, bỏ mục rác ("a,", "a.").
_STOP = set("""la gi cua va cac nhung mot cho voi thi ma o tai trong ve nay do khi nao sao the nhu bao nhieu
duoc co khong em anh chi minh ban hay giup xin a oi vay roi nhe lam thay ko k dc j z""".split())
_VIETE = re.compile(r"\bvi\s*-?\s*[eéè]te?\b")
_SYMBOLS = {"δ": " delta ", "∆": " delta ", "√": " can ", "≥": " >= ", "≤": " <= "}


def _terms(text: str) -> list:
    """Tách từ + bigram. Mỗi từ là {"a": dạng có dấu, "p": dạng không dấu, "f": túi dùng khi từ này nằm trong câu hỏi}.
    "f" = "a" nếu người gõ có dấu, "p" nếu gõ không dấu. Bigram có dấu khi một trong hai từ có dấu."""
    text = unicodedata.normalize("NFC", (text or "").lower())
    for sym, word in _SYMBOLS.items():
        text = text.replace(sym, word)
    text = _VIETE.sub("viet", text)  # "Viète" / "Vi-ét" / "viete" / "viet" → cùng một từ
    words = []
    for w in re.findall(r"\w+", text):
        plain = strip_accents(w)
        if plain in _STOP or plain.isdigit() or not re.fullmatch(r"[a-z0-9]+", plain):
            continue
        words.append({"a": w, "p": plain, "f": "a" if w != plain else "p"})
    bigrams = [{"a": x["a"] + "_" + y["a"], "p": x["p"] + "_" + y["p"], "f": "a" if "a" in (x["f"], y["f"]) else "p"}
               for x, y in zip(words, words[1:])]
    return words + bigrams


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
    text = re.sub(r"\\[()\[\]]", " ", text)
    text = re.sub(r"\\([{}])", r"\1", text).replace("$", "")
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"(?<=[+-])\s+(?=[\d.])", "", text)
    text = re.sub(r"\s*/\s*", "/", text)
    # Strip a bounded number of literal-value wrappers, never evaluate expressions.
    for _ in range(8):
        unwrapped = re.sub(r"\(\s*(" + _LEAK_VALUE + r")\s*\)", r"\1", text)
        if unwrapped == text:
            break
        text = unwrapped
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


_LEAK_FACTOR = re.compile(r"\(\s*x\s*([+-])\s*(" + _LEAK_NUMBER + r")\s*\)")


def _leak_factor_roots(text):
    """Nghiệm lộ qua dạng nhân tử có số cụ thể: (x - 2)(x + 3) → {2, -3}. Thêm bởi Khoa sau thử tấn công.
    Chỉ đọc nhân tử dạng (x ± số); (2x - 1) hay (x - r) bằng chữ không tính."""
    roots = set()
    for sign, literal in _LEAK_FACTOR.findall(text):
        value = _leak_fraction(literal)
        if value is not None:
            roots.add(value if sign == "-" else -value)
    return roots


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
    for line in normalized.splitlines():
        if re.fullmatch(r"\s*" + _LEAK_VALUE + r"\s*[.!]?\s*", line):
            roots.update(_leak_values(line, roots_only=False))
    roots.update(_leak_factor_roots(normalized))
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
    Cùng ý với citations trong app/backend/app/agents/tutor.py (chỉ giữ nguồn có thật trong đoạn đã truy xuất). Owner: Ninh (N-03).
    - Bắt MỌI thẻ [Nguồn: ...] (cả "nguồn"/"Nguon", nhiều mã trong một thẻ cách nhau bằng ";" hoặc ",").
    - Mã đoạn không nằm trong `chunks` → bỏ (nguồn bịa). Mã đúng nhưng ghi sai trang → sửa về trang thật của đoạn.
    - Thẻ giữ lại được viết lại đúng dạng chuẩn [Nguồn: <mã> - Trang <số>] để bộ chấm grounding đọc được.
    - Output: {"reply", "sources": [{"code","page"}] (không trùng, theo thứ tự xuất hiện),
      "removed": [thẻ bịa đã bỏ], "fixed": [mã bị sửa trang]} — 2 khoá sau để ghi trace, agent không bắt buộc dùng."""
    valid = {c["code"].upper(): (c["code"], c["page"]) for c in chunks or [] if c.get("code")}  # không phân biệt hoa thường
    sources, seen, removed, fixed = [], set(), [], []

    def rewrite(m):
        kept = []
        for part in re.split(r"[;,]", m.group(1)):
            ref = _CITE_REF.match(part.strip())
            code = ref.group(1).upper() if ref else ""
            if code not in valid:
                if part.strip():
                    removed.append(part.strip())
                continue
            code, page = valid[code]
            if ref.group(2) and int(ref.group(2)) != page:
                fixed.append(code)
            kept.append("%s - Trang %s" % (code, page))
            if code not in seen:
                seen.add(code)
                sources.append({"code": code, "page": page})
        return " ".join("[Nguồn: %s]" % k for k in kept)  # mỗi nguồn một thẻ: bộ chấm grounding đọc 1 mã / thẻ

    clean = _CITE_TAG.sub(rewrite, reply or "")
    if removed:
        clean = re.sub(r"[ \t]+([.,;:!?)])", r"\1", re.sub(r"[ \t]{2,}", " ", clean))  # dọn khoảng trắng sau khi bỏ thẻ
        note("citations: bỏ %d thẻ nguồn bịa: %s" % (len(removed), "; ".join(removed)[:200]))
    if fixed:
        note("citations: sửa trang cho %s" % ", ".join(fixed))
    return {"reply": clean, "sources": sources, "removed": removed, "fixed": fixed}


_CITE_TAG = re.compile(r"\[\s*ngu[ồo]n\s*:\s*([^\]]*)\]", re.I)
_CITE_REF = re.compile(r"([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)(?:\s*[-–,]?\s*(?:trang|tr\.?|p\.?)\s*(\d+))?", re.I)


@tool
def flag_message(message: str, mode: str = "hint") -> str:
    """flag_message · Input: tin nhắn học sinh, chế độ ("hint"/"answer") · Output: lý do gắn cờ hoặc None ·
    Không tác động ra ngoài. CHỈ ĐỂ GẮN CỜ cho giáo viên xem lại và ghi note() vào trace: KHÔNG chặn, KHÔNG đổi chế độ —
    luật chặn nằm ở system prompt (prompts.py) và chốt check_leak. Owner: Ninh (N-03).
    Cùng ý với flag_message trong app/backend/app/agents/tutor.py, thêm loại "impersonation" và so cả câu gõ không dấu.
    Thứ tự ưu tiên (trả lý do đầu tiên khớp):
      "jailbreak"     bỏ qua / quên hướng dẫn, đóng vai AI khác, chế độ nhà phát triển, đòi in system prompt / đáp án mẫu
      "impersonation" tự nhận là giáo viên / admin, hoặc "thầy cô cho phép rồi"
      "ask_answer"    xin đáp án / đáp số / lời giải, "giải hộ" — chỉ tính khi mode="hint" (hết hạn thì xin là hợp lệ)"""
    text = message or ""
    plain = strip_accents(text)
    if _JAILBREAK.search(plain) or _DAN.search(text):
        return "jailbreak"
    if _IMPERSONATE.search(plain):
        return "impersonation"
    if mode == "hint" and _ASK_ANSWER.search(plain):
        return "ask_answer"
    return None


# Các mẫu viết KHÔNG DẤU vì so trên strip_accents(tin nhắn): bắt được cả "bỏ qua hướng dẫn" lẫn "bo qua huong dan".
_JAILBREAK = re.compile(
    r"(bo qua|quen|phot lo|lo di|dung theo|khong can theo|ignore|disregard|forget|override)\W*(\w+\W+){0,4}?"
    r"(huong dan|quy tac|luat|chi dan|chi thi|cau lenh|lenh truoc|instruction|rule|prompt)"
    r"|system prompt|developer mode|che do (nha phat trien|developer|admin|khong gioi han)|jailbreak"
    r"|dong vai|you are now|act as|pretend|bay gio ban la|ban la (mot )?ai khac|khong (con )?gioi han"
    r"|(in|hien|cho xem|tiet lo|nhac lai|print|show|reveal)\W+(ra\W+)?(nguyen van\W+)?(\w+\W+){0,2}?"
    r"(system prompt|prompt|dap an mau|huong dan (he thong|goc)|dap_an_mau)")
_DAN = re.compile(r"\bDAN\b")  # so trên bản CÓ DẤU, phân biệt hoa thường: "dẫn" bỏ dấu cũng thành "dan"
_IMPERSONATE = re.compile(
    r"\b(toi|minh|ta|day|em)\W+(la|dang la|chinh la)\W+(\w+\W+){0,1}?(giao vien|thay giao|co giao|gv|admin|quan tri|giam thi)"
    r"|\b(i am|i'm)\W+(the|a|your)?\W*(teacher|admin)"
    r"|\b(thay|co|giao vien|gv|thay co)\W+(\w+\W+){0,2}?(da\W+)?(cho phep|dong y|bao|cho)\W+(\w+\W+){0,4}?"
    r"(dap an|dap so|loi giai|ket qua|xem|giai)")
_ASK_ANSWER = re.compile(
    r"\b(cho|xin|dua|gui|noi|in|bao)\W+(\w+\W+){0,3}?(dap an|dap so|ket qua|loi giai|nghiem cuoi)"
    r"|\bgiai\W+(ho|giup|ho em|chi tiet|het|luon|full)\b|\blam\W+(ho|giup)\b|\bdap (an|so)\W+(\w+\W+){0,2}?de\W+(so|doi chieu|kiem tra)")


# ---------- So đề: tin nhắn có chứa đề của một bài CÒN HẠN không (chống "mượn" bài đã hết hạn để xin giải) ----------
_PROBLEM_SUBS = [
    (r"\\left|\\right|\\,|\\;|\\!|\$", ""), (r"\\cdot|\\times|·|×", "*"), (r"[−–﹣]", "-"),
    (r"²", "^2"), (r"³", "^3"), (r"\^\{\s*(\d)\s*\}", r"^\1"), (r"\*\*", "^"),
    (r"(?<=\d),(?=\d)", "."),  # "2,5" là số thập phân; dấu phẩy còn lại là dấu câu
]
_EQUATION = re.compile(r"([0-9x\^\+\-\*\./\s\(\)]{1,60})=([0-9x\^\+\-\*\./\s\(\)]{1,60})")
_POLY_TERM = re.compile(r"([+-]?)(\d+(?:\.\d+)?(?:/\d+)?)?\*?(x(?:\^(\d))?)?")


def _poly(side):
    """'2x^2 - 3x + 1' → {2: 2, 1: -3, 0: 1} (Fraction). Không đọc được (ngoặc, bậc > 3…) → None."""
    s = side.replace(" ", "").rstrip(".")
    if not s or "(" in s or ")" in s:
        return None
    out, pos = {}, 0
    while pos < len(s):
        m = _POLY_TERM.match(s, pos)
        if not m or m.end() == pos or (not m.group(2) and not m.group(3)):
            return None
        coef = Fraction(m.group(2)) if m.group(2) else Fraction(1)
        if m.group(1) == "-":
            coef = -coef
        deg = (int(m.group(4)) if m.group(4) else 1) if m.group(3) else 0
        if deg > 3:
            return None
        out[deg] = out.get(deg, 0) + coef
        pos = m.end()
    return out


def problem_keys(text: str) -> set:
    """Các "dấu vân tay" phương trình trong một đoạn chữ, chuẩn hoá để nhận ra cùng một đề:
    chuyển hết về một vế, chia cho ước chung, hệ số bậc cao nhất dương → 'x^2 - 5x + 6 = 0', '6 - 5x + x² = 0',
    '2x^2 - 10x + 12 = 0' cho cùng một khoá. Bỏ qua dòng nghiệm kiểu 'x = 3' (bậc 1, vế trái chỉ có x).
    Không bắt được thì không có khoá (không đoán)."""
    t = (text or "").lower()
    for pat, rep in _PROBLEM_SUBS:  # trước NFKC: NFKC đổi "x²" thành "x2"
        t = re.sub(pat, rep, t)
    t = unicodedata.normalize("NFKC", t)
    keys = set()
    for left, right in _EQUATION.findall(t):
        if "x" not in left + right:
            continue
        a, b = _poly(left), _poly(right)
        if a is None or b is None:
            continue
        diff = {d: a.get(d, 0) - b.get(d, 0) for d in set(a) | set(b)}
        diff = {d: c for d, c in diff.items() if c}
        if not diff or max(diff) < 1:
            continue
        if max(diff) == 1 and len(diff) <= 2 and left.strip() == "x":
            continue  # 'x = 3' là kết luận nghiệm, không phải một đề
        lead = diff[max(diff)]
        coefs = tuple(diff.get(d, Fraction(0)) / lead for d in range(max(diff), -1, -1))
        keys.add("poly:" + ",".join(str(c) for c in coefs))
    return keys


def same_problem(message: str, candidates: list) -> list:
    """Các bài trong candidates (mỗi bài có "question") mà đề trùng với một phương trình trong message."""
    mine = problem_keys(message)
    return [c for c in candidates if mine & problem_keys(c.get("question", ""))] if mine else []


@tool
def check_open_assignments(message: str, class_id: str, now: str, exclude_id: str = None) -> dict:
    """check_open_assignments · Input: tin nhắn, mã lớp, giờ hỏi (ISO), mã bài đang mở (bỏ qua) ·
    Output: {"matches": [{"id","title","due_at"}], "final_answers": [str]} — các bài CÒN HẠN cùng lớp có đề trùng
    phương trình học sinh gửi, kèm đáp án cuối của chúng để check_leak chặn · Không tác động ra ngoài. Owner: Ninh.
    Dùng ở chế độ answer: học sinh mở bài đã hết hạn rồi dán đề bài còn hạn → agent chuyển về hint cho lượt đó."""
    now_dt = _parse_dt(now)
    opens = [a for a in _load("assignments.json")
             if a.get("class_id") == class_id and a.get("id") != exclude_id and _parse_dt(a["due_at"]) > now_dt]
    hits = same_problem(message, opens)
    return {"matches": [{"id": a["id"], "title": a["title"], "due_at": a["due_at"]} for a in hits],
            "final_answers": [f for a in hits for f in a.get("final_answers", [])]}


# ---------- Chốt chặn cuối theo CÂU TRẢ LỜI: đáp án của mọi bài CÒN HẠN khác (chống lách bằng cách viết đề bằng chữ) ----------
def leak_targets(other_finals: list, own_finals: list) -> list:
    """Đáp án cuối của các bài CÒN HẠN khác, trừ phần trùng với đáp án của chính bài đang mở, ở dạng check_leak đọc được.

    other_finals: list các list đáp án (mỗi bài một list, như final_answers_of). own_finals: đáp án bài đang mở
    (rỗng nếu không có). Trả ["x = 2", "25", ...]. Dùng để soi câu trả lời ở MỌI chế độ: học sinh có thể dán / gõ
    đề bài còn hạn theo bất kỳ cách nào (vd "x bình phương trừ 5x cộng 6 bằng 0") mà so đề không nhận ra; nghiệm
    lộ ra trong câu trả lời thì vẫn bắt được. Nghiệm trùng với bài đang mở không chặn được (không phân biệt được) —
    giới hạn đã biết. Chỉ tính toán, không tác động ra ngoài.
    """
    def roots(answers):
        out = set()
        for a in answers or []:
            if isinstance(a, str) and a.strip():
                out |= _leak_values(_leak_normalize(a).strip(), roots_only=True)
        return out

    def scalars(answers):
        return {_leak_fraction(a.strip()) for a in answers or []
                if isinstance(a, str) and re.fullmatch(_LEAK_NUMBER, _leak_normalize(a).strip())}

    own_roots, own_scalars = roots(own_finals), scalars(own_finals)
    out = set()
    for answers in other_finals or []:
        out |= {"x = %s" % r for r in roots(answers) - own_roots}
        out |= {str(s) for s in scalars(answers) - own_scalars}
    return sorted(out)


# ---------- Kiểm bước làm của học sinh bằng code (lượt 2: B16 — model tính nhẩm Delta sai rồi xác nhận bước sai) ----------
_STEP_NUM = r"(-?\s*\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)"
_COEF = {k: re.compile(r"(?<![a-z])%s\s*=\s*%s" % (k, _STEP_NUM)) for k in "abc"}
_DELTA_LINE = re.compile(r"(?:delta|Δ|∆)\s*=([^\n]*)", re.I)


def _quadratic(text):
    """(a, b, c) của phương trình bậc hai đầu tiên trong đề (đưa hết về một vế, GIỮ nguyên hệ số). Không đọc được → None."""
    t = (text or "").lower()
    for pat, rep in _PROBLEM_SUBS:
        t = re.sub(pat, rep, t)
    t = unicodedata.normalize("NFKC", t)
    for left, right in _EQUATION.findall(t):
        p, q = _poly(left.strip()), _poly(right.strip())
        if p is None or q is None:
            continue
        d = {k: p.get(k, 0) - q.get(k, 0) for k in set(p) | set(q)}
        if d.get(2):
            return Fraction(d[2]), Fraction(d.get(1, 0)), Fraction(d.get(0, 0))
    return None


def _frac(s):
    try:
        return Fraction(s.replace(" ", "").replace(",", "."))
    except (ValueError, ZeroDivisionError):
        return None


@tool
def check_steps(message: str, question: str) -> dict:
    """check_steps · Input: tin nhắn học sinh, đề bài · Output: {"notes": [str], "first_error": str|None}.
    Chỉ tính toán (Fraction, không làm tròn), không tác động ra ngoài. Lượt 2 (Khoa).

    Đọc các bước học sinh tự ghi "a = …, b = …, c = …" và "Delta = … = <số>", so với hệ số của đề và
    Delta = b² − 4ac tính bằng code. Ghi chú KHÔNG nêu giá trị Delta đúng hay nghiệm — chỉ nói bước nào khớp / lệch
    và lệch ở đâu, để model khỏi tính nhẩm (lỗi B16 lượt 1). Học sinh nhân / chia cả phương trình cho cùng một số
    (hệ số tỉ lệ với đề) vẫn được coi là đúng và Delta được kiểm theo hệ số của học sinh.
    """
    notes, first = [], None
    q = _quadratic(question)
    msg = unicodedata.normalize("NFKC", (message or "").replace("−", "-").replace("–", "-"))
    got = {k: _frac(m.group(1)) for k, rx in _COEF.items() for m in [rx.search(msg)] if m}
    if q is None or (not got and not _DELTA_LINE.search(msg)):
        return {"notes": [], "first_error": None}
    a0, b0, c0 = q
    coefs = (a0, b0, c0)
    # Học sinh tự viết lại phương trình (vd nhân −1): không tương đương đề → đó là bước sai đầu tiên;
    # các bước sau được kiểm theo CHÍNH phương trình học sinh viết.
    mine = _quadratic(msg)
    if mine and mine != q:
        k = mine[0] / a0
        if (mine[1], mine[2]) == (b0 * k, c0 * k):
            coefs = mine
        else:
            notes.append("Phương trình sau biến đổi học sinh ghi: KHÔNG tương đương đề (khi nhân / chia hay chuyển vế phải "
                         "đổi đủ mọi hạng tử, kể cả hằng số). Đây là bước sai đầu tiên.")
            first = "bien_doi"
            coefs = mine
    if len(got) == 3 and None not in got.values():
        ga, gb, gc = got["a"], got["b"], got["c"]
        a0, b0, c0 = coefs
        k = ga / a0 if a0 else None
        if k and (gb, gc) == (b0 * k, c0 * k):
            notes.append("Hệ số a, b, c học sinh ghi: KHỚP với đề" + ("" if k == 1 else " (đã nhân cả phương trình với cùng một số — hợp lệ)") + ".")
            coefs = (ga, gb, gc)
        else:
            wrong = [n for n, g, t in (("a", ga, a0), ("b", gb, b0), ("c", gc, c0)) if g != t]
            signs = [n for n, g, t in (("a", ga, a0), ("b", gb, b0), ("c", gc, c0)) if g == -t and g != 0]
            msg_err = "Hệ số học sinh ghi: SAI ở %s" % ", ".join(wrong)
            if signs:
                msg_err += " (sai DẤU — hệ số phải lấy cả dấu đứng trước trong đề)"
            notes.append(msg_err + (". Đây là bước sai đầu tiên." if first is None else "."))
            first = first or "he_so"
            coefs = (ga, gb, gc)  # kiểm Delta theo chính hệ số học sinh dùng, để biết có thêm lỗi tính không
    m = _DELTA_LINE.search(msg)
    if m:
        nums = re.findall(_STEP_NUM, m.group(1).split("rồi")[0].split(",")[0])
        claimed = _frac(nums[-1]) if nums else None
        a, b, c = coefs
        truth = b * b - 4 * a * c
        if claimed is not None:
            if claimed == truth:
                notes.append("Delta học sinh ghi: ĐÚNG theo các hệ số %s." % ("của đề" if first is None else
                             "học sinh đang dùng (nhưng các hệ số đó đã sai từ bước trước)"))
            else:
                hint = "kiểm lại công thức b² − 4ac và dấu của −4ac"
                if "+ 4ac" in m.group(1).replace(" ", " ") or "+4ac" in m.group(1).replace(" ", ""):
                    hint = "học sinh dùng b² + 4ac — sai CÔNG THỨC"
                elif a * c < 0:
                    hint = "a và c trái dấu nên −4ac là số DƯƠNG (phép trừ thành phép cộng) — học sinh tính sai dấu này"
                notes.append("Delta học sinh ghi: SAI (%s). KHÔNG nêu giá trị Delta đúng, để học sinh tự tính lại." % hint)
                first = first or "delta"
    if notes:
        note("check_steps: %s" % " | ".join(notes))
    return {"notes": notes, "first_error": first}
