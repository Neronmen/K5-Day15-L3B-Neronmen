"""Dựng system prompt cho Knowledge Agent (bên bài giảng) và Socratic Tutor (khung bài tập)."""
import re
from dataclasses import dataclass

from .policy import TutorMode
from .prompts import ANSWER_MODE, GROUNDING, HINT_MODE, LECTURE_CONTEXT, OUTSIDE_EXTENDED, OUTSIDE_STRICT

CITE_RE = re.compile(r"\[Nguồn:\s*([^\]]+?)\s*\]")

# Dấu hiệu cố bẻ khoá — chỉ để gắn cờ cho giáo viên xem lại; luật chặn nằm ở system prompt
_JAILBREAK = re.compile(
    r"(bỏ qua|quên|phớt lờ|ignore|disregard|forget).{0,30}(hướng dẫn|quy tắc|luật|chỉ dẫn|instruction|rule|prompt)"
    r"|system prompt|developer mode|chế độ nhà phát triển|jailbreak|DAN\b|đóng vai.{0,20}(giáo viên|admin|AI khác)"
    r"|you are now|bây giờ bạn là",
    re.I,
)
_ASK_ANSWER = re.compile(r"(cho|xin|đưa|gửi|nói).{0,15}(đáp án|kết quả|lời giải)|giải (hộ|giúp|chi tiết|hết)|làm (hộ|giúp)", re.I)


@dataclass
class AssignmentCtx:
    title: str
    prompt: str
    reference_answer: str | None


def flag_message(text: str, mode: str) -> str | None:
    if _JAILBREAK.search(text):
        return "jailbreak"
    if mode == "hint" and _ASK_ANSWER.search(text):
        return "ask_answer"
    return None


def build_system(*, chunks: list[dict], ai_mode: str, mode: TutorMode | None = None,
                 assignment: AssignmentCtx | None = None) -> str:
    """mode=None: chat bên bài giảng. mode='hint'/'answer': khung bài tập (Rule 3)."""
    outside = OUTSIDE_EXTENDED if ai_mode == "extended" else OUTSIDE_STRICT
    system = GROUNDING.format(outside_rule=outside)
    if assignment is None:
        system += LECTURE_CONTEXT
    else:
        system += HINT_MODE if mode == "hint" else ANSWER_MODE
        system += f"\n\n<bai_tap>\n{assignment.title}\n{assignment.prompt}\n</bai_tap>"
        # Đáp án mẫu chỉ vào ngữ cảnh sau deadline → khi còn hạn AI không có gì để lộ
        if mode == "answer" and assignment.reference_answer:
            system += f"\n\n<dap_an_mau>\n{assignment.reference_answer}\n</dap_an_mau>"
    docs = "\n".join(f'<doan nguon="{c["source_label"]}">\n{c["text"]}\n</doan>' for c in chunks)
    system += f"\n\n<tai_lieu>\n{docs or '(không có đoạn nào liên quan)'}\n</tai_lieu>"
    return system


def citations(answer: str, chunks: list[dict]) -> list[dict]:
    """Chỉ trả các thẻ nguồn có thật trong đoạn đã truy xuất (chặn nguồn bịa)."""
    allowed = {c["source_label"]: c for c in chunks}
    out, seen = [], set()
    for label in CITE_RE.findall(answer):
        c = allowed.get(label)
        if c and label not in seen:
            seen.add(label)
            out.append({"label": label, "document_id": c["document_id"], "page_number": c["page_number"]})
    return out
