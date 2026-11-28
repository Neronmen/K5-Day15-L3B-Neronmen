"""Tóm tắt lịch sử hỏi AI theo học sinh: cờ đỏ đếm bằng code, AI không hạ được mức cảnh báo."""
from app.routers.chat_insights import RANK, _code_level


def test_code_level_counts_flags():
    assert _code_level({}) == "ok"
    assert _code_level({"ask_answer": 1}) == "watch"
    assert _code_level({"ask_answer": 2}) == "alert"
    assert _code_level({"impersonation": 1}) == "alert"


def test_ai_cannot_lower_code_level():
    assert max("ok", _code_level({"jailbreak": 1}), key=RANK.get) == "alert"
