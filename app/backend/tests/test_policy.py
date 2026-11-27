from datetime import datetime, timedelta, timezone

from app.agents.policy import get_tutor_mode

NOW = datetime(2026, 11, 21, 21, 0, tzinfo=timezone.utc)


def test_student_before_deadline_gets_hints():
    assert get_tutor_mode("student", NOW + timedelta(minutes=1), NOW) == "hint"


def test_student_after_deadline_gets_answer():
    assert get_tutor_mode("student", NOW, NOW) == "answer"


def test_teacher_always_gets_answer():
    assert get_tutor_mode("teacher", NOW + timedelta(days=1), NOW) == "answer"
